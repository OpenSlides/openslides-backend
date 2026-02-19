from typing import Any, Optional

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.keycloak_admin_client import KeycloakAdminClient
from ....shared.mixins.user_scope_mixin import UserScopeMixin
from ....shared.oidc_config import get_oidc_config
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .password_mixins import ClearSessionsMixin


class UserResetPasswordToDefaultMixin(
    UpdateAction, CheckForArchivedMeetingMixin, ClearSessionsMixin
):
    def _get_keycloak_client(self) -> Optional[KeycloakAdminClient]:
        """
        Create a Keycloak Admin API client using client credentials.
        """
        oidc_config = get_oidc_config()

        if not oidc_config.enabled or not oidc_config.admin_api_enabled:
            return None

        if not oidc_config.admin_api_url:
            return None

        if not oidc_config.admin_client_id or not oidc_config.admin_client_secret:
            return None

        return KeycloakAdminClient(
            admin_api_url=oidc_config.admin_api_url,
            client_id=oidc_config.admin_client_id,
            client_secret=oidc_config.admin_client_secret,
            logger=self.logger,
        )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Gets the default_password and reset password.
        """
        instance = super().update_instance(instance)
        user = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["default_password", "saml_id", "keycloak_id"],
            lock_result=False,
        )
        if user.get("saml_id"):
            raise ActionException(
                f"user {user['saml_id']} is a Single Sign On user and has no local OpenSlides password."
            )
        plaintext_password = str(user.get("default_password"))
        default_password = self.auth.hash(plaintext_password)
        instance["password"] = default_password

        # Sync password to Keycloak if user has keycloak_id
        keycloak_id = user.get("keycloak_id")
        if keycloak_id:
            client = self._get_keycloak_client()
            if client:
                # Raises ActionException on failure -> action fails
                client.set_password(keycloak_id, plaintext_password)

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
