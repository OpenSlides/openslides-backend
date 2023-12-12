from typing import Any, Dict, Iterable, Optional

import fastjsonschema

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.interfaces.event import Event
from ....shared.schema import schema_version
from ....shared.typing import Schema
from ....shared.util import ONE_ORGANIZATION_ID
from ...generics.create import CreateAction
from ...generics.update import UpdateAction
from ...mixins.send_email_mixin import EmailCheckMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.action_type import ActionType
from ...util.register import register_action
from ...util.typing import ActionData, ActionResultElement
from .user_mixins import UsernameMixin

allowed_user_fields = [
    "saml_id",
    "title",
    "first_name",
    "last_name",
    "email",
    "gender",
    "pronoun",
    "is_active",
    "is_physical_person",
]


@register_action("user.save_saml_account", action_type=ActionType.STACK_INTERNAL)
class UserSaveSamlAccount(
    EmailCheckMixin, UsernameMixin, CreateAction, UpdateAction, SingularActionMixin
):
    """
    Internal action to save (create or update) a saml account.
    It should be called from the auth service.
    """

    user: Dict[str, Any] = {}
    saml_attr_mapping: Dict[str, str]
    check_email_field = "email"
    model = User()
    schema: Schema = {}
    skip_archived_meeting_check = True

    def validate_instance(self, instance: Dict[str, Any]) -> None:
        organization = self.datastore.get(
            ONE_ORGANIZATION_FQID,
            ["saml_enabled", "saml_attr_mapping"],
            lock_result=False,
        )
        if not organization.get("saml_enabled"):
            raise ActionException(
                "SingleSignOn is not enabled in OpenSlides configuration"
            )
        self.saml_attr_mapping = organization.get("saml_attr_mapping", {})
        if not self.saml_attr_mapping or not isinstance(self.saml_attr_mapping, dict):
            raise ActionException(
                "SingleSignOn field attributes are not configured in OpenSlides"
            )
        self.schema = {
            "$schema": schema_version,
            "title": "create saml account schema",
            "type": "object",
            "properties": {
                payload_field: {
                    "oneOf": [
                        (type_def := self.model.get_field(model_field).get_schema()),
                        {
                            "type": "array",
                            "items": type_def,
                            "minItems": 1 if model_field == "saml_id" else 0,
                        },
                    ]
                }
                for model_field, payload_field in self.saml_attr_mapping.items()
                if model_field in allowed_user_fields
            },
            "required": [self.saml_attr_mapping["saml_id"]],
            "additionalProperties": True,
        }
        try:
            fastjsonschema.validate(self.schema, instance)
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(exception.message)

    def validate_fields(self, instance_old: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms the payload fields into model fields, removes the possible array-wrapped format
        """
        instance: Dict[str, Any] = dict()
        for model_field, payload_field in self.saml_attr_mapping.items():
            if payload_field in instance_old and model_field in allowed_user_fields:
                value = (
                    tx[0]
                    if isinstance((tx := instance_old[payload_field]), list) and len(tx)
                    else tx
                )
                if value not in (None, []):
                    instance[model_field] = value

        return super().validate_fields(instance)

    def prepare_action_data(self, action_data: ActionData) -> ActionData:
        """Necessary to prevent id reservation in CreateAction's prepare_action_data"""
        return action_data

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        users = self.datastore.filter(
            "user",
            FilterOperator("saml_id", "=", instance["saml_id"]),
            ["id", *allowed_user_fields],
        )
        if len(users) == 1:
            self.user = next(iter(users.values()))
            instance["id"] = self.user["id"]
        elif len(users) == 0:
            instance["id"] = self.datastore.reserve_ids(self.model.collection, 1)[0]
            instance = self.set_defaults(instance)
        else:
            ActionException(
                f"More than one existing user found in database with saml_id {instance['saml_id']}"
            )

        return UpdateAction.base_update_instance(self, instance)

    def create_events(self, instance: Dict[str, Any]) -> Iterable[Event]:
        """
        Handles create and update
        """
        if "meta_new" in instance:
            yield from CreateAction.create_events(self, instance)
        else:
            fields = {
                k: v for k, v in instance.items() if k == "id" or v != self.user.get(k)
            }
            yield from UpdateAction.create_events(self, fields)

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        return {"user_id": instance["id"]}

    def set_defaults(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if "is_active" not in instance:
            instance["is_active"] = True
        if "is_physical_person" not in instance:
            instance["is_physical_person"] = True
        instance["can_change_own_password"] = False
        instance["organization_id"] = ONE_ORGANIZATION_ID
        instance["username"] = self.generate_usernames([instance.get("saml_id", "")])[0]
        instance["meta_new"] = True
        return super().set_defaults(instance)
