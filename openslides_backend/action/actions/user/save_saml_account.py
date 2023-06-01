from typing import Any, Dict, Iterable, Optional, cast

import fastjsonschema

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....models.fields import Field
from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.interfaces.event import Event, EventType
from ....shared.patterns import fqid_from_collection_and_id
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
from .user_mixin import UsernameMixin

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
    EmailCheckMixin, UsernameMixin, CreateAction, SingularActionMixin
):
    """
    Internal action to save (create or update) a saml account.
    It should be called from the auth service.
    """

    user: Dict[str, Any] = {}
    saml_attr_mapping: Dict[str, str]
    check_email_field = "email"
    model = User()
    schema: Schema
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
        additional_required_fields = {
            value: {
                "oneOf": [
                    (type_def := self.model.saml_id.get_payload_schema()),
                    {"type": "array", "items": type_def, "minItems": 1},
                ]
            }
            for key, value in self.saml_attr_mapping.items()
            if key == "saml_id"
        }
        additional_optional_fields = {
            value: {
                "oneOf": [
                    (
                        type_def := cast(
                            Field, getattr(self.model, key, {})
                        ).get_payload_schema()
                    ),
                    {"type": "array", "items": type_def},
                ]
            }
            for key, value in self.saml_attr_mapping.items()
            if key != "saml_id" and key in allowed_user_fields
        }
        self.schema = {
            "$schema": schema_version,
            "title": "create saml account schema",
            "type": "object",
            "properties": {
                **additional_required_fields,
                **additional_optional_fields,
            },
            "required": list(additional_required_fields.keys()),
            "additionalProperties": True,
        }
        try:
            fastjsonschema.validate(self.schema, instance)
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(exception.message)

    def prepare_action_data(self, action_data: ActionData) -> ActionData:
        """Necessary to prevent id reservation in CreateAction's prepare_action_data"""
        return action_data

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass

    def base_update_instance(self, instance_old: Dict[str, Any]) -> Dict[str, Any]:
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
            instance["can_change_own_password"] = False
            instance["organization_id"] = ONE_ORGANIZATION_ID
            instance["username"] = self.generate_usernames([instance["saml_id"]])[0]
            instance["meta_new"] = True
            instance = self.set_defaults(instance)
        else:
            ActionException(
                f"More than one existing user found in database with saml_id {instance['saml_id']}"
            )

        instance = self.validate_fields(instance)
        instance = self.update_instance(instance)
        self.apply_instance(instance)
        self.validate_relation_fields(instance)
        # Return id of user anyway
        self.results.append(self.create_action_result_element(instance))
        return instance

    def create_events(self, instance: Dict[str, Any]) -> Iterable[Event]:
        """
        Handles create and update
        """
        fqid = fqid_from_collection_and_id(self.model.collection, instance["id"])
        if "meta_new" in instance:
            del instance["meta_new"]
            yield self.build_event(EventType.Create, fqid, instance)
        else:
            fields = UpdateAction.create_update_events(instance)
            if not fields:
                return []
            fields = {k: v for k, v in instance.items() if v != self.user.get(k)}
            if not fields:
                return []
            yield self.build_event(EventType.Update, fqid, fields)

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        return {"user_id": instance["id"]}
