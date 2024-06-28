from collections.abc import Iterable
from typing import Any, cast

import fastjsonschema

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.interfaces.event import Event
from ....shared.schema import schema_version
from ....shared.typing import Schema
from ...mixins.meeting_user_helper import get_meeting_user
from ...mixins.send_email_mixin import EmailCheckMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.action_type import ActionType
from ...util.register import register_action
from ...util.typing import ActionData, ActionResultElement
from .create import UserCreate
from .update import UserUpdate
from .user_mixins import UsernameMixin

allowed_user_fields = [
    "saml_id",
    "title",
    "first_name",
    "last_name",
    "email",
    "gender_id",
    "pronoun",
    "is_active",
    "is_physical_person",
]


@register_action("user.save_saml_account", action_type=ActionType.STACK_INTERNAL)
class UserSaveSamlAccount(
    EmailCheckMixin,
    UsernameMixin,
    SingularActionMixin,
):
    """
    Internal action to save (create or update) a saml account.
    It should be called from the auth service.
    """

    user: dict[str, Any] = {}
    saml_attr_mapping: dict[str, str]
    check_email_field = "email"
    model = User()
    schema: Schema = {}
    skip_archived_meeting_check = True

    def validate_instance(self, instance: dict[str, Any]) -> None:
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

    def validate_fields(self, instance_old: dict[str, Any]) -> dict[str, Any]:
        """
        Transforms the payload fields into model fields, removes the possible array-wrapped format
        """
        instance: dict[str, Any] = dict()
        for model_field, payload_field in self.saml_attr_mapping.items():
            if (
                isinstance(payload_field, str)
                and payload_field in instance_old
                and model_field in allowed_user_fields
            ):
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

    def check_permissions(self, instance: dict[str, Any]) -> None:
        pass

    def base_update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        meeting_id, group_id = self.check_for_group_add()
        users = self.datastore.filter(
            "user",
            FilterOperator("saml_id", "=", instance["saml_id"]),
            ["id", *allowed_user_fields],
        )
        if len(users) == 1:
            self.user = next(iter(users.values()))
            instance["id"] = (user_id := cast(int, self.user["id"]))
            if meeting_id and group_id:
                meeting_user = get_meeting_user(
                    self.datastore, meeting_id, user_id, ["id", "group_ids"]
                )
                if meeting_user:
                    old_group_ids = meeting_user["group_ids"]
                    if group_id not in old_group_ids:
                        instance["meeting_id"] = meeting_id
                        instance["group_ids"] = old_group_ids + [group_id]
                else:
                    instance["meeting_id"] = meeting_id
                    instance["group_ids"] = [group_id]

            instance = {
                k: v for k, v in instance.items() if k == "id" or v != self.user.get(k)
            }
            if len(instance) > 1:
                self.execute_other_action(UserUpdate, [instance])
        elif len(users) == 0:
            instance = self.set_defaults(instance)
            if group_id:
                instance["meeting_id"] = meeting_id
                instance["group_ids"] = [group_id]
            self.execute_other_action(UserCreate, [instance])
        else:
            ActionException(
                f"More than one existing user found in database with saml_id {instance['saml_id']}"
            )
        return instance

    def create_events(self, instance: dict[str, Any]) -> Iterable[Event]:
        """
        delegated to execute_other_actions
        """
        return []

    def create_action_result_element(
        self, instance: dict[str, Any]
    ) -> ActionResultElement | None:
        return {"user_id": instance["id"]}

    def set_defaults(self, instance: dict[str, Any]) -> dict[str, Any]:
        if "is_active" not in instance:
            instance["is_active"] = True
        if "is_physical_person" not in instance:
            instance["is_physical_person"] = True
        instance["can_change_own_password"] = False
        instance["username"] = self.generate_usernames([instance.get("saml_id", "")])[0]
        return instance

    def check_for_group_add(self) -> tuple[int, int] | tuple[None, None]:
        NoneResult = (None, None)
        if not (
            meeting_info := cast(dict, self.saml_attr_mapping.get("meeting"))
        ) or not (external_id := meeting_info.get("external_id")):
            return NoneResult

        meetings = self.datastore.filter(
            collection="meeting",
            filter=FilterOperator("external_id", "=", external_id),
            mapped_fields=["id", "default_group_id"],
        )
        if len(meetings) == 1:
            meeting = next(iter(meetings.values()))
            group_id = meeting["default_group_id"]
        else:
            self.logger.warning(
                f"save_saml_account found {len(meetings)} meetings with external_id '{external_id}'"
            )
            return NoneResult
        if external_group_id := meeting_info.get("external_group_id"):
            groups = self.datastore.filter(
                collection="group",
                filter=And(
                    [
                        FilterOperator("external_id", "=", external_group_id),
                        FilterOperator("meeting_id", "=", meeting.get("id")),
                    ]
                ),
                mapped_fields=["id"],
            )
            if len(groups) == 1:
                group_id = next(iter(groups.keys()))
            else:
                self.logger.warning(
                    f"save_saml_account found no group in meeting '{external_id}' for '{external_group_id}', but use default_group of meeting"
                )
        if not group_id:
            self.logger.warning(
                f"save_saml_account found no group in meeting '{external_id}' for '{external_group_id}'"
            )
            return NoneResult
        return meeting.get("id"), group_id
