from typing import Any, Dict

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import ActionException
from ....shared.mixins.user_scope_mixin import UserScopeMixin
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


class UserSetPasswordMixin(UpdateAction, CheckForArchivedMeetingMixin):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        set hashed password and set default password if set_as_default is True.
        """
        user = self.datastore.get(
            f"user/{instance['id']}", ["saml_id"], lock_result=False
        )
        if user.get("saml_id"):
            raise ActionException(
                f"user {user['saml_id']} is a Single Sign On user and has no local Openslides passwort."
            )

        password = instance.pop("password")
        set_as_default = False
        if "set_as_default" in instance:
            set_as_default = instance.pop("set_as_default")
        hashed_password = self.auth.hash(password)
        instance["password"] = hashed_password
        if set_as_default:
            instance["default_password"] = password
        return instance


@register_action("user.set_password")
class UserSetPasswordAction(
    UserSetPasswordMixin,
    UserScopeMixin,
):
    """
    Action to set the password and default_pasword.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        required_properties=["password"],
        additional_optional_fields={"set_as_default": {"type": "boolean"}},
    )
    history_information = "Password changed"
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        self.check_permissions_for_scope(instance["id"])
