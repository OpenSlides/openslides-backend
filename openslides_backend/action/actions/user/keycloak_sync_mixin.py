from typing import Any, Optional

from ....shared.keycloak_admin_client import KeycloakAdminClient
from ....shared.oidc_config import get_oidc_config
from ....shared.patterns import fqid_from_collection_and_id
from ...action import Action

# Fields that are synchronized to Keycloak (Keycloak-leading)
# Maps OpenSlides field names to Keycloak field names
KEYCLOAK_SYNC_FIELDS = {
    "email": "email",
    "username": "username",
    "is_active": "enabled",
    "first_name": "firstName",
    "last_name": "lastName",
}


class KeycloakSyncMixin(Action):
    """
    Synchronizes user changes to Keycloak BEFORE the DB commit.

    When updating users that have a keycloak_id and Keycloak sync is enabled,
    this mixin will update the corresponding Keycloak user first. If the
    Keycloak update fails, the entire action fails.
    """

    def _get_keycloak_client(self) -> Optional[KeycloakAdminClient]:
        """
        Create a Keycloak Admin API client using client credentials.

        Uses the configured admin client credentials to obtain a token
        via client credentials grant. The client must have service account
        enabled and realm-admin role for user management.

        Returns:
            KeycloakAdminClient if Keycloak sync is enabled and configured,
            None otherwise.
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

    def _get_keycloak_id(self, user_id: int) -> Optional[str]:
        """Get keycloak_id for a user."""
        user = self.datastore.get(
            fqid_from_collection_and_id("user", user_id),
            ["keycloak_id"],
            lock_result=False,
        )
        return user.get("keycloak_id")

    def _has_keycloak_sync_fields(self, instance: dict[str, Any]) -> bool:
        """Check if any Keycloak-leading fields are being changed."""
        return any(field in instance for field in KEYCLOAK_SYNC_FIELDS)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """Sync to Keycloak BEFORE DB update for Keycloak-leading fields."""
        instance = super().update_instance(instance)

        user_id = instance.get("id")
        if not user_id:
            return instance

        # Only sync if Keycloak-leading fields are being changed
        if not self._has_keycloak_sync_fields(instance):
            return instance

        keycloak_id = self._get_keycloak_id(user_id)
        if not keycloak_id:
            return instance  # Not a Keycloak user

        client = self._get_keycloak_client()
        if not client:
            return instance  # Keycloak sync not enabled

        # Build Keycloak update data
        kc_data: dict[str, Any] = {}
        for os_field, kc_field in KEYCLOAK_SYNC_FIELDS.items():
            if os_field in instance:
                kc_data[kc_field] = instance[os_field]

        if kc_data:
            # Raises ActionException on failure -> action fails
            client.update_user(keycloak_id, kc_data)

        return instance


class KeycloakDeleteSyncMixin(Action):
    """
    Deletes user in Keycloak BEFORE the DB delete.

    When deleting users that have a keycloak_id and Keycloak sync is enabled,
    this mixin will delete the corresponding Keycloak user first. If the
    Keycloak deletion fails, the entire action fails.
    """

    def _get_keycloak_client(self) -> Optional[KeycloakAdminClient]:
        """
        Create a Keycloak Admin API client using client credentials.

        Uses the configured admin client credentials to obtain a token
        via client credentials grant. The client must have service account
        enabled and realm-admin role for user management.

        Returns:
            KeycloakAdminClient if Keycloak sync is enabled and configured,
            None otherwise.
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
        """Delete user in Keycloak BEFORE DB delete."""
        instance = super().update_instance(instance)

        user_id = instance.get("id")
        if not user_id:
            return instance

        user = self.datastore.get(
            fqid_from_collection_and_id("user", user_id),
            ["keycloak_id"],
            lock_result=False,
        )
        keycloak_id = user.get("keycloak_id")

        if not keycloak_id:
            return instance  # Not a Keycloak user

        client = self._get_keycloak_client()
        if not client:
            return instance  # Keycloak sync not enabled

        # Raises ActionException on failure -> deletion fails
        client.delete_user(keycloak_id)

        return instance


class KeycloakCreateSyncMixin(Action):
    """
    Creates user in Keycloak during user.create action.

    When OIDC admin API is enabled and no keycloak_id is provided,
    this mixin will create a corresponding Keycloak user and store
    the returned keycloak_id on the OpenSlides user.
    """

    def _get_keycloak_client(self) -> Optional[KeycloakAdminClient]:
        """
        Create a Keycloak Admin API client using client credentials.

        Uses the configured admin client credentials to obtain a token
        via client credentials grant. The client must have service account
        enabled and realm-admin role for user management.

        Returns:
            KeycloakAdminClient if Keycloak sync is enabled and configured,
            None otherwise.
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
        """Create user in Keycloak and store keycloak_id."""
        instance = super().update_instance(instance)

        # Skip if user already has a keycloak_id (SSO user) or saml_id
        if instance.get("keycloak_id") or instance.get("saml_id"):
            return instance

        client = self._get_keycloak_client()
        if not client:
            return instance  # Keycloak sync not enabled

        # Build Keycloak user data
        kc_data: dict[str, Any] = {}
        for os_field, kc_field in KEYCLOAK_SYNC_FIELDS.items():
            if os_field in instance and instance[os_field] is not None:
                kc_data[kc_field] = instance[os_field]

        # Ensure username is always provided
        if "username" not in kc_data and "username" in instance:
            kc_data["username"] = instance["username"]

        if not kc_data.get("username"):
            return instance  # Cannot create user without username

        # Create user in Keycloak - raises ActionException on failure
        keycloak_id = client.create_user(kc_data)

        # Store keycloak_id and set can_change_own_password to False
        instance["keycloak_id"] = keycloak_id
        instance["can_change_own_password"] = False

        # Set password in Keycloak if default_password is provided
        default_password = instance.get("default_password")
        if default_password:
            client.set_password(keycloak_id, default_password)

        return instance


class KeycloakPasswordSyncMixin(Action):
    """
    Synchronizes password changes to Keycloak.

    When changing password for users that have a keycloak_id and
    Keycloak sync is enabled, this mixin will also set the password
    in Keycloak. The plaintext password must be stored in the instance
    before hashing (stored in _keycloak_password attribute).
    """

    def _get_keycloak_client(self) -> Optional[KeycloakAdminClient]:
        """
        Create a Keycloak Admin API client using client credentials.

        Uses the configured admin client credentials to obtain a token
        via client credentials grant. The client must have service account
        enabled and realm-admin role for user management.

        Returns:
            KeycloakAdminClient if Keycloak sync is enabled and configured,
            None otherwise.
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

    def _get_keycloak_id(self, user_id: int) -> Optional[str]:
        """Get keycloak_id for a user."""
        user = self.datastore.get(
            fqid_from_collection_and_id("user", user_id),
            ["keycloak_id"],
            lock_result=False,
        )
        return user.get("keycloak_id")

    def set_password(self, instance: dict[str, Any]) -> None:
        """
        Override to capture plaintext password before hashing and sync to Keycloak.
        """
        # Capture plaintext password before it gets hashed
        plaintext_password = instance.get("password")

        # Call parent's set_password which will hash the password
        super().set_password(instance)  # type: ignore

        # Now sync to Keycloak if applicable
        if plaintext_password:
            self._sync_password_to_keycloak(instance, plaintext_password)

    def _sync_password_to_keycloak(
        self, instance: dict[str, Any], plaintext_password: str
    ) -> None:
        """Sync password to Keycloak for users with keycloak_id."""
        user_id = instance.get("id")
        if not user_id:
            return

        keycloak_id = self._get_keycloak_id(user_id)
        if not keycloak_id:
            return  # Not a Keycloak user

        client = self._get_keycloak_client()
        if not client:
            return  # Keycloak sync not enabled

        # Raises ActionException on failure -> action fails
        client.set_password(keycloak_id, plaintext_password)
