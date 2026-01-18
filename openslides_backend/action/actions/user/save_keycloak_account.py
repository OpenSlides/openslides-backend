"""
Action to save (create or update) a Keycloak/OIDC account.

This action is called internally for OIDC user provisioning.
"""

from collections.abc import Iterable
from typing import Any

import fastjsonschema

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.interfaces.event import Event
from ....shared.schema import schema_version
from ....shared.typing import Schema
from ...mixins.send_email_mixin import EmailCheckMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.action_type import ActionType
from ...util.register import register_action
from ...util.typing import ActionData, ActionResultElement
from ..gender.create import GenderCreate
from .create import UserCreate
from .update import UserUpdate
from .user_mixins import UsernameMixin

# Mapping from OIDC/Keycloak user-info claims to OpenSlides user fields
# external (OIDC claim) : internal (OpenSlides field)
allowed_user_fields = {
    "keycloak_id": "keycloak_id",  # sub claim
    "title": "title",
    "first_name": "given_name",  # Standard OIDC claim
    "last_name": "family_name",  # Standard OIDC claim
    "email": "email",
    "gender": "gender_id",
    "pronoun": "pronoun",
    "is_active": "is_active",
    "is_physical_person": "is_physical_person",
    "member_number": "member_number",
}

# Standard OIDC claims mapping
OIDC_CLAIM_MAPPING = {
    "keycloak_id": "sub",
    "email": "email",
    "given_name": "given_name",
    "family_name": "family_name",
    "preferred_username": "preferred_username",
    "name": "name",
}


@register_action("user.save_keycloak_account", action_type=ActionType.STACK_INTERNAL)
class UserSaveKeycloakAccount(
    EmailCheckMixin,
    UsernameMixin,
    SingularActionMixin,
):
    """
    Internal action to save (create or update) a Keycloak/OIDC account.
    It should be called from the OIDC authentication flow.
    """

    user: dict[str, Any] = {}
    oidc_attr_mapping: dict[str, str]
    check_email_field = "email"
    model = User()
    schema: Schema = {}
    skip_archived_meeting_check = True

    def validate_instance(self, instance: dict[str, Any]) -> None:
        organization = self.datastore.get(
            ONE_ORGANIZATION_FQID,
            ["oidc_enabled", "oidc_attr_mapping"],
            lock_result=False,
        )
        if not organization.get("oidc_enabled"):
            raise ActionException(
                "OIDC authentication is not enabled in OpenSlides configuration"
            )

        # Use custom mapping from organization, or default OIDC claim mapping
        self.oidc_attr_mapping = organization.get("oidc_attr_mapping") or {}
        if not isinstance(self.oidc_attr_mapping, dict):
            self.oidc_attr_mapping = {}

        # Build schema for validation
        self.schema = {
            "$schema": schema_version,
            "title": "create keycloak account schema",
            "type": "object",
            "properties": {
                "keycloak_id": {"type": "string", "minLength": 1},
                "email": {"type": "string"},
                "given_name": {"type": "string"},
                "family_name": {"type": "string"},
                "preferred_username": {"type": "string"},
                "name": {"type": "string"},
            },
            "required": ["keycloak_id"],
            "additionalProperties": True,
        }

        try:
            fastjsonschema.validate(self.schema, instance)
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(exception.message)

    def validate_fields(self, instance_old: dict[str, Any]) -> dict[str, Any]:
        """
        Transforms the OIDC user-info fields into OpenSlides user fields.
        """
        instance: dict[str, Any] = {}

        # Map keycloak_id from sub claim
        instance["keycloak_id"] = instance_old.get("keycloak_id") or instance_old.get(
            "sub"
        )

        # Map email
        if email := instance_old.get("email"):
            instance["email"] = email

        # Map name fields using custom mapping or defaults
        first_name_field = self.oidc_attr_mapping.get("first_name", "given_name")
        last_name_field = self.oidc_attr_mapping.get("last_name", "family_name")

        if first_name := instance_old.get(first_name_field):
            instance["first_name"] = first_name
        if last_name := instance_old.get(last_name_field):
            instance["last_name"] = last_name

        # Store preferred_username for later use in username generation
        if preferred_username := instance_old.get("preferred_username"):
            instance["_preferred_username"] = preferred_username

        return super().validate_fields(instance)

    def prepare_action_data(self, action_data: ActionData) -> ActionData:
        """Necessary to prevent id reservation in CreateAction's prepare_action_data"""
        return action_data

    def check_permissions(self, instance: dict[str, Any]) -> None:
        # No permission check needed for internal action
        pass

    def base_update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        # Look up user by keycloak_id
        users = self.datastore.filter(
            "user",
            FilterOperator("keycloak_id", "=", instance["keycloak_id"]),
            [
                "id",
                "gender_id",
                *allowed_user_fields.keys(),
            ],
        )

        # Handle gender if provided
        if gender := instance.pop("gender", None):
            gender_dict = self.datastore.filter(
                "gender",
                FilterOperator("name", "=", gender),
                ["id"],
            )
            gender_id = None
            if gender_dict:
                gender_id = next(iter(gender_dict.keys()))
            else:
                action_result = self.execute_other_action(
                    GenderCreate, [{"name": gender}]
                )
                if action_result and action_result[0]:
                    gender_id = action_result[0].get("id", 0)
            if gender_id:
                instance["gender_id"] = gender_id
            else:
                self.logger.warning(
                    f"save_keycloak_account could neither find nor create {gender}. Not handling gender."
                )
        elif gender == "":
            instance["gender_id"] = None

        # Remove internal fields
        preferred_username = instance.pop("_preferred_username", None)

        user_id = None
        if len(users) == 1:
            # User exists - update
            self.user = next(iter(users.values()))
            instance["id"] = user_id = self.user["id"]

            # Only update fields that have changed
            instance = {
                k: v for k, v in instance.items() if k == "id" or v != self.user.get(k)
            }
            if len(instance) > 1:
                self.execute_other_action(UserUpdate, [instance])
        elif len(users) == 0:
            # User doesn't exist - create
            instance = self.set_defaults(instance, preferred_username)
            response = self.execute_other_action(UserCreate, [instance])
            if response and response[0]:
                user_id = response[0].get("id")
                instance["id"] = user_id
        else:
            raise ActionException(
                f"More than one existing user found in database with keycloak_id {instance['keycloak_id']}"
            )

        return instance

    def create_events(self, instance: dict[str, Any]) -> Iterable[Event]:
        """
        Delegated to execute_other_action
        """
        return []

    def create_action_result_element(
        self, instance: dict[str, Any]
    ) -> ActionResultElement | None:
        return {"user_id": instance.get("id")}

    def set_defaults(
        self, instance: dict[str, Any], preferred_username: str | None
    ) -> dict[str, Any]:
        if "is_active" not in instance:
            instance["is_active"] = True
        if "is_physical_person" not in instance:
            instance["is_physical_person"] = True

        # Keycloak users cannot change their password locally
        instance["can_change_own_password"] = False

        # Generate username
        if preferred_username:
            instance["username"] = self.generate_usernames([preferred_username])[0]
        elif instance.get("keycloak_id"):
            instance["username"] = self.generate_usernames([instance["keycloak_id"]])[0]
        else:
            # Fallback to first_name + last_name or keycloak_id
            name_parts = []
            if instance.get("first_name"):
                name_parts.append(instance["first_name"])
            if instance.get("last_name"):
                name_parts.append(instance["last_name"])
            if name_parts:
                instance["username"] = self.generate_usernames(
                    ["_".join(name_parts).lower()]
                )[0]
            else:
                instance["username"] = self.generate_usernames(["oidc_user"])[0]

        return instance
