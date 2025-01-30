from typing import Any

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.mixins.user_scope_mixin import UserScopeMixin
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .password_mixins import ClearSessionsMixin


class UserResetPasswordToDefaultMixin(
    UpdateAction, CheckForArchivedMeetingMixin, ClearSessionsMixin
):
    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Gets the default_password and reset password.
        """
        instance = super().update_instance(instance)
        user = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["default_password", "saml_id"],
            lock_result=False,
        )
        if user.get("saml_id"):
            raise ActionException(
                f"user {user['saml_id']} is a Single Sign On user and has no local OpenSlides password."
            )
        default_password = self.auth.hash(str(user.get("default_password")))
        instance["password"] = default_password
        return instance


@register_action("user.reset_password_to_default")
class UserResetPasswordToDefaultAction(
    UserResetPasswordToDefaultMixin,
    UserScopeMixin,
):
    """
    Action to reset a password to default of a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS

    def check_permissions(self, instance: dict[str, Any]) -> None:
        self.check_permissions_for_scope(
            instance["id"], meeting_permission=Permissions.User.CAN_UPDATE
        )
