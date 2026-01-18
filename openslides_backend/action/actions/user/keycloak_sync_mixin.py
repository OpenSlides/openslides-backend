from typing import Any, Optional

from ....shared.keycloak_admin_client import KeycloakAdminClient
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.util import ONE_ORGANIZATION_FQID
from ...action import Action

# Fields that are synchronized to Keycloak (Keycloak-leading)
# Maps OpenSlides field names to Keycloak field names
KEYCLOAK_SYNC_FIELDS = {
    "email": "email",
    "username": "username",
    "is_active": "enabled",
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
        Create a Keycloak Admin API client using the user's access token.

        Returns:
            KeycloakAdminClient if Keycloak sync is enabled and configured,
            None otherwise.
        """
        org = self.datastore.get(
            ONE_ORGANIZATION_FQID,
            ["oidc_enabled", "oidc_admin_api_enabled", "oidc_admin_api_url"],
            lock_result=False,
        )

        if not org.get("oidc_enabled") or not org.get("oidc_admin_api_enabled"):
            return None

        admin_api_url = org.get("oidc_admin_api_url")
        if not admin_api_url:
            return None

        access_token = self.services.authentication().access_token
        if not access_token:
            return None

        return KeycloakAdminClient(
            admin_api_url=admin_api_url,
            access_token=access_token,
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
        Create a Keycloak Admin API client using the user's access token.

        Returns:
            KeycloakAdminClient if Keycloak sync is enabled and configured,
            None otherwise.
        """
        org = self.datastore.get(
            ONE_ORGANIZATION_FQID,
            ["oidc_enabled", "oidc_admin_api_enabled", "oidc_admin_api_url"],
            lock_result=False,
        )

        if not org.get("oidc_enabled") or not org.get("oidc_admin_api_enabled"):
            return None

        admin_api_url = org.get("oidc_admin_api_url")
        if not admin_api_url:
            return None

        access_token = self.services.authentication().access_token
        if not access_token:
            return None

        return KeycloakAdminClient(
            admin_api_url=admin_api_url,
            access_token=access_token,
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
