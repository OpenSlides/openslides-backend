"""
Migration: Migrate existing local users to Keycloak.

This migration creates corresponding Keycloak users for all local users
(those without keycloak_id and saml_id) when KEYCLOAK_ADMIN_API_URL is configured.

Environment variables:
- KEYCLOAK_ADMIN_API_URL: Required. Keycloak Admin API URL (e.g., http://keycloak:8080/auth/admin/realms/openslides)
- KEYCLOAK_ADMIN_USERNAME: Admin username (default: "admin")
- KEYCLOAK_ADMIN_PASSWORD: Admin password (default: "admin")

The migration:
1. Acquires an admin token from Keycloak
2. For each local user (no keycloak_id, no saml_id):
   - Creates user in Keycloak with matching username, email, firstName, lastName, enabled
   - Imports Argon2 password hash directly via Keycloak credential API
   - For SHA512 legacy hashes: sets default_password as temporary password
   - Updates user_t with keycloak_id and sets can_change_own_password=FALSE
"""

import json
import os
from typing import Any, Optional

import requests
from psycopg import Cursor
from psycopg.rows import DictRow

from openslides_backend.migrations.migration_helper import (
    MigrationHelper,
    MigrationState,
)

# Collections affected by this migration (empty since we don't use replace tables)
ORIGIN_COLLECTIONS: list[str] = []


def _get_admin_token(base_url: str, username: str, password: str) -> str:
    """
    Get admin access token from Keycloak master realm.

    Args:
        base_url: Keycloak admin API URL (e.g., http://keycloak:8080/auth/admin/realms/openslides)
        username: Admin username
        password: Admin password

    Returns:
        Access token string

    Raises:
        RuntimeError: If token acquisition fails
    """
    # Derive token URL from admin URL
    # admin_url: http://keycloak:8080/auth/admin/realms/openslides
    # token_url: http://keycloak:8080/auth/realms/master/protocol/openid-connect/token
    parts = base_url.split("/admin/")
    if len(parts) != 2:
        raise RuntimeError(
            f"Invalid KEYCLOAK_ADMIN_API_URL format: {base_url}. "
            "Expected format: http://host/auth/admin/realms/realmname"
        )
    token_url = f"{parts[0]}/realms/master/protocol/openid-connect/token"

    response = requests.post(
        token_url,
        data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": username,
            "password": password,
        },
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to get Keycloak admin token: {response.status_code} - {response.text}"
        )

    return response.json()["access_token"]


def _create_keycloak_user(
    admin_url: str, token: str, user_data: dict[str, Any]
) -> Optional[str]:
    """
    Create a user in Keycloak.

    Args:
        admin_url: Keycloak admin API URL
        token: Admin access token
        user_data: User data including credentials

    Returns:
        Keycloak user ID (UUID) or None on failure
    """
    response = requests.post(
        f"{admin_url}/users",
        json=user_data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    if response.status_code == 201:
        # Extract keycloak_id from Location header
        location = response.headers.get("Location", "")
        return location.split("/")[-1] if location else None
    elif response.status_code == 409:
        # Conflict - user already exists
        return None
    else:
        MigrationHelper.write_line(
            f"  Failed to create user: {response.status_code} - {response.text}"
        )
        return None


def _get_keycloak_user_by_username(
    admin_url: str, token: str, username: str
) -> Optional[dict[str, Any]]:
    """
    Find a Keycloak user by username.

    Args:
        admin_url: Keycloak admin API URL
        token: Admin access token
        username: Username to search for

    Returns:
        User data dict or None if not found
    """
    response = requests.get(
        f"{admin_url}/users",
        params={"username": username, "exact": "true"},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    if response.status_code == 200:
        users = response.json()
        return users[0] if users else None
    return None


def _build_argon2_credential(password_hash: str) -> dict[str, Any]:
    """
    Build Keycloak credential data for an Argon2 password hash.

    Keycloak 21+ supports importing Argon2 hashes via the credential API.

    Args:
        password_hash: Argon2 password hash (e.g., $argon2id$v=19$m=65536,t=3,p=4$...)

    Returns:
        Keycloak credential object
    """
    return {
        "type": "password",
        "credentialData": json.dumps({"algorithm": "argon2", "hashIterations": 1}),
        "secretData": json.dumps({"value": password_hash, "salt": ""}),
    }


def _build_plaintext_credential(password: str, temporary: bool = False) -> dict[str, Any]:
    """
    Build Keycloak credential data for a plaintext password.

    Keycloak will hash this using its configured algorithm.

    Args:
        password: Plaintext password
        temporary: If True, user must change password on next login

    Returns:
        Keycloak credential object
    """
    return {
        "type": "password",
        "value": password,
        "temporary": temporary,
    }


def _is_argon2_hash(password_hash: str) -> bool:
    """Check if password hash is Argon2 format."""
    return password_hash.startswith("$argon2")


def _is_sha512_hash(password_hash: str) -> bool:
    """
    Check if password hash is SHA512 format (legacy).

    SHA512 hashes have 64-byte salt prefix + base64 hash = 152 characters total.
    """
    return not password_hash.startswith("$argon2") and len(password_hash) == 152


def data_manipulation(curs: Cursor[DictRow]) -> None:
    """
    Migrate local users to Keycloak if KEYCLOAK_ADMIN_API_URL is configured.

    This migration:
    1. Checks if Keycloak admin API is configured via KEYCLOAK_ADMIN_API_URL
    2. Acquires admin token via password grant to master realm
    3. Queries users without keycloak_id AND without saml_id
    4. For each user:
       - Creates in Keycloak with username, email, firstName, lastName, enabled
       - Imports Argon2 password hash directly via Keycloak credential API
       - For SHA512/no password: uses default_password if available
       - Updates user_t with keycloak_id, sets can_change_own_password=FALSE
    5. Logs progress and summary
    """
    admin_api_url = os.environ.get("KEYCLOAK_ADMIN_API_URL", "")

    if not admin_api_url:
        MigrationHelper.write_line(
            "KEYCLOAK_ADMIN_API_URL not set - skipping Keycloak user migration"
        )
        MigrationHelper.set_database_migration_info(
            curs, 101, MigrationState.FINALIZATION_REQUIRED
        )
        return

    MigrationHelper.write_line(f"Keycloak Admin API URL: {admin_api_url}")

    admin_username = os.environ.get("KEYCLOAK_ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "admin")

    # Get admin token
    try:
        token = _get_admin_token(admin_api_url, admin_username, admin_password)
        MigrationHelper.write_line("Successfully acquired Keycloak admin token")
    except RuntimeError as e:
        MigrationHelper.write_line(f"ERROR: {e}")
        MigrationHelper.write_line("Skipping Keycloak user migration due to auth failure")
        MigrationHelper.set_database_migration_info(
            curs, 101, MigrationState.FINALIZATION_REQUIRED
        )
        return

    # Query local users (no keycloak_id, no saml_id)
    curs.execute(
        """
        SELECT id, username, email, first_name, last_name, is_active, password, default_password
        FROM user_t
        WHERE keycloak_id IS NULL AND saml_id IS NULL
        ORDER BY id
        """
    )
    users = curs.fetchall()

    if not users:
        MigrationHelper.write_line("No local users to migrate")
        MigrationHelper.set_database_migration_info(
            curs, 101, MigrationState.FINALIZATION_REQUIRED
        )
        return

    MigrationHelper.write_line(f"Found {len(users)} local users to migrate")

    # Statistics
    migrated = 0
    linked = 0
    skipped = 0
    failed = 0

    for user in users:
        user_id = user["id"]
        username = user["username"]
        email = user.get("email")
        first_name = user.get("first_name")
        last_name = user.get("last_name")
        is_active = user.get("is_active", True)
        password_hash = user.get("password")
        default_password = user.get("default_password")

        MigrationHelper.write_line(f"Processing user {user_id}: {username}")

        # Build Keycloak user data
        kc_user_data: dict[str, Any] = {
            "username": username,
            "enabled": is_active if is_active is not None else True,
            "requiredActions": [],
        }

        if email:
            kc_user_data["email"] = email
        if first_name:
            kc_user_data["firstName"] = first_name
        if last_name:
            kc_user_data["lastName"] = last_name

        # Handle password/credentials
        credentials: list[dict[str, Any]] = []

        if password_hash and _is_argon2_hash(password_hash):
            # Argon2 hash - import directly
            credentials.append(_build_argon2_credential(password_hash))
            MigrationHelper.write_line(f"  Using Argon2 hash for {username}")
        elif default_password:
            # Use default_password as plaintext (Keycloak hashes it)
            # Set as non-temporary since user knows this password
            credentials.append(_build_plaintext_credential(default_password, temporary=False))
            MigrationHelper.write_line(
                f"  Using default_password for {username}"
            )
        elif password_hash and _is_sha512_hash(password_hash):
            # SHA512 legacy hash - cannot import, skip credential
            # User will need to use "forgot password" flow
            MigrationHelper.write_line(
                f"  WARNING: SHA512 hash for {username} cannot be migrated. User will need password reset."
            )
        else:
            # No password - user will need to use "forgot password" flow
            MigrationHelper.write_line(
                f"  No password for {username}. User will need password reset."
            )

        if credentials:
            kc_user_data["credentials"] = credentials

        # Create user in Keycloak
        keycloak_id = _create_keycloak_user(admin_api_url, token, kc_user_data)

        if keycloak_id:
            # Successfully created - update OpenSlides user
            curs.execute(
                """
                UPDATE user_t
                SET keycloak_id = %s, can_change_own_password = FALSE
                WHERE id = %s
                """,
                (keycloak_id, user_id),
            )
            MigrationHelper.write_line(
                f"  Created Keycloak user for {username}: {keycloak_id}"
            )
            migrated += 1
        else:
            # Failed or conflict - try to find existing user and link
            existing_user = _get_keycloak_user_by_username(admin_api_url, token, username)
            if existing_user:
                keycloak_id = existing_user.get("id")
                if keycloak_id:
                    curs.execute(
                        """
                        UPDATE user_t
                        SET keycloak_id = %s, can_change_own_password = FALSE
                        WHERE id = %s
                        """,
                        (keycloak_id, user_id),
                    )
                    MigrationHelper.write_line(
                        f"  Linked existing Keycloak user for {username}: {keycloak_id}"
                    )
                    linked += 1
                else:
                    MigrationHelper.write_line(
                        f"  ERROR: Could not get ID for existing user {username}"
                    )
                    failed += 1
            else:
                MigrationHelper.write_line(
                    f"  ERROR: Failed to create or find user {username}"
                )
                failed += 1

    # Summary
    MigrationHelper.write_line("")
    MigrationHelper.write_line("Migration Summary:")
    MigrationHelper.write_line(f"  Created: {migrated}")
    MigrationHelper.write_line(f"  Linked to existing: {linked}")
    MigrationHelper.write_line(f"  Skipped: {skipped}")
    MigrationHelper.write_line(f"  Failed: {failed}")
    MigrationHelper.write_line(f"  Total: {len(users)}")

    MigrationHelper.set_database_migration_info(
        curs, 101, MigrationState.FINALIZATION_REQUIRED
    )
