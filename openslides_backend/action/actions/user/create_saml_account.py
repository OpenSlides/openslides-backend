from typing import Any, Dict

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.util import ONE_ORGANIZATION_ID
from ...generics.create import CreateAction
from ...mixins.send_email_mixin import EmailCheckMixin
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .user_mixin import UsernameMixin


@register_action("user.create_saml_account", action_type=ActionType.STACK_INTERNAL)
class UserCreateSamlAccount(EmailCheckMixin, UsernameMixin, CreateAction):
    """
    Internal action to create a saml account.
    It should be called from the auth service.
    """

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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance["username"] = self.generate_usernames([instance["saml_id"]])[0]
        if self.datastore.exists(
            "user", FilterOperator("saml_id", "=", instance["saml_id"])
        ):
            raise ActionException("Saml_id already exists.")

        instance["can_change_own_password"] = False
        instance["organization_id"] = ONE_ORGANIZATION_ID
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
