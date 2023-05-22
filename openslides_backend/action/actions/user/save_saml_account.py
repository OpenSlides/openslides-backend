from typing import Any, Dict, Iterable

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.interfaces.event import Event, EventType
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.util import ONE_ORGANIZATION_ID
from ...generics.create import CreateAction
from ...mixins.send_email_mixin import EmailCheckMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .user_mixin import UsernameMixin


@register_action("user.save_saml_account", action_type=ActionType.STACK_INTERNAL)
class UserSaveSamlAccount(
    EmailCheckMixin, UsernameMixin, CreateAction, SingularActionMixin
):
    """
    Internal action to save (create or update) a saml account.
    It should be called from the auth service.
    """

    check_email_field = "email"
    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        required_properties=["saml_id"],
        optional_properties=[
            "title",
            "first_name",
            "last_name",
            "email",
            "gender",
            "pronoun",
            "is_active",
            "is_physical_person",
        ],
        title="create saml account schema",
    )
    skip_archived_meeting_check = True

    def validate_instance(self, instance: Dict[str, Any]) -> None:
        organization = self.datastore.get(
            ONE_ORGANIZATION_FQID,
            ["sso_enabled", "sso_attr_mapping"],
            lock_result=False,
        )
        if not organization.get("sso_enabled"):
            raise ActionException(
                "SingleSignOn is not enabled in OpenSlides configuration"
            )
        if not (
            sso_attr_mapping := organization.get("sso_attr_mapping")
        ) or not isinstance(sso_attr_mapping, dict):
            raise ActionException(
                "SingleSignOn field attributes are not configured in OpenSlides"
            )
        new_instance = {
            sso_attr_mapping[key]: value
            for key, value in instance.items()
            if key in sso_attr_mapping
            and sso_attr_mapping[key] in self.schema["properties"].keys()
        }
        instance.clear()
        instance.update(new_instance)
        super().validate_instance(instance)

    def prepare_action_data(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            users = self.datastore.filter(
                "user", FilterOperator("saml_id", "=", instance["saml_id"]), ["id"]
            )
            if len(users) == 1:
                instance["id"] = next(iter(users.values()))["id"]
            elif len(users) == 0:
                instance["id"] = self.datastore.reserve_ids(self.model.collection, 1)[0]
                instance["can_change_own_password"] = False
                instance["organization_id"] = ONE_ORGANIZATION_ID
                instance["username"] = self.generate_usernames([instance["saml_id"]])[0]
                instance["meta_new"] = True
            else:
                ActionException(
                    f"More than one existing user found in database with saml_id {instance['saml_id']}"
                )
        return action_data

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if "meta_new" in instance:
            instance = self.set_defaults(instance)
        instance = self.validate_fields(instance)

        instance = self.update_instance(instance)
        self.apply_instance(instance)
        self.validate_relation_fields(instance)

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
            fields = {
                k: v
                for k, v in instance.items()
                if k != "id" and not k.startswith("meta_")
            }
            if not fields:
                return []
            yield self.build_event(EventType.Update, fqid, fields)
