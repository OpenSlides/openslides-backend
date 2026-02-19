from typing import Any

from ....action.generics.update import UpdateAction
from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permissions import Permissions
from ....shared.mixins.user_scope_mixin import UserScopeMixin
from ...util.crypto import get_random_password
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionResultElement
from .keycloak_sync_mixin import KeycloakPasswordSyncMixin
from .password_mixins import ClearSessionsMixin, SetPasswordMixin


@register_action("user.generate_new_password")
class UserGenerateNewPassword(
    KeycloakPasswordSyncMixin,
    SetPasswordMixin,
    CheckForArchivedMeetingMixin,
    UserScopeMixin,
    ClearSessionsMixin,
    UpdateAction,
):
    model = User()
    schema = DefaultSchema(User()).get_update_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS

    # Store the generated password to return in the result
    _generated_passwords: dict[int, str]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._generated_passwords = {}

    def check_permissions(self, instance: dict[str, Any]) -> None:
        self.check_permissions_for_scope(
            instance["id"], meeting_permission=Permissions.User.CAN_UPDATE
        )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Generates new password and call the super code.
        """
        password = get_random_password()
        instance["password"] = password
        instance["set_as_default"] = True
        # Store for returning in result
        self._generated_passwords[instance["id"]] = password
        self.set_password(instance)
        return instance

    def create_action_result_element(
        self, instance: dict[str, Any]
    ) -> ActionResultElement | None:
        """Return the generated password so the client can display it."""
        user_id = instance.get("id")
        if user_id and user_id in self._generated_passwords:
            return {"id": user_id, "password": self._generated_passwords[user_id]}
        return {"id": user_id}
