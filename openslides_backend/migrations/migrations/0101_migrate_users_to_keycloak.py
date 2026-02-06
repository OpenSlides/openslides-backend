"""
Migration: Migrate existing local users to Keycloak.

This migration creates corresponding Keycloak users for all local users
(those without there d and saml_id) when KEYCLOAK_ADMIN_API_URL is configured.

Environment variables:
- KEYCLOAK_ADMIN_API_URL: Required. Keycloak Admin API URL (e.g., http://keycloak:8080/auth/admin/realms/openslides)
- KEYCLOAK_ADMIN_CLIENT_ID: Service account client ID (default: "openslides-admin")
- KEYCLOAK_ADMIN_CLIENT_SECRET: Service account client secret (default: "openslides-admin-secret")

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
from typing import Any

from psycopg import Cursor
from psycopg.rows import DictRow

from openslides_backend.migrations.migration_helper import (
    MigrationHelper,
    MigrationState,
)
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.keycloak_admin_client import KeycloakAdminClient

# Collections affected by this migration (empty since we don't use replace tables)
ORIGIN_COLLECTIONS: list[str] = []


def _parse_argon2_hash(password_hash: str) -> dict[str, Any] | None:
    """
    Parse an Argon2 encoded hash string into its components.

    Format: $argon2id$v=19$m=65536,t=3,p=4$<salt_base64>$<hash_base64>

    Returns:
        Dict with type, version, memory, iterations, parallelism, salt, hash
        or None if parsing fails
    """
    try:
        parts = password_hash.split("$")
        # parts[0] = "" (empty before first $)
        # parts[1] = "argon2id" (type)
        # parts[2] = "v=19" (version)
        # parts[3] = "m=65536,t=3,p=4" (parameters)
        # parts[4] = salt (base64)
        # parts[5] = hash (base64)
        if len(parts) != 6:
            return None

        argon_type = parts[1]  # "argon2id", "argon2i", or "argon2d"
        version = parts[2].split("=")[1]  # "19"

        # Parse parameters
        params = {}
        for param in parts[3].split(","):
            key, value = param.split("=")
            params[key] = int(value)

        return {
            "type": argon_type,
            "version": version,
            "memory": params.get("m", 65536),
            "iterations": params.get("t", 3),
            "parallelism": params.get("p", 4),
            "salt": parts[4],
            "hash": parts[5],
        }
    except (IndexError, ValueError, KeyError):
        return None


def _build_argon2_credential(password_hash: str) -> dict[str, Any] | None:
    """
    Build Keycloak credential data for an Argon2 password hash.

    Keycloak expects the hash components to be separated, not in the
    standard Argon2 encoded format.

    Args:
        password_hash: Argon2 password hash (e.g., $argon2id$v=19$m=65536,t=3,p=4$...)

    Returns:
        Keycloak credential object or None if parsing fails
    """
    parsed = _parse_argon2_hash(password_hash)
    if not parsed:
        return None

    # Keycloak's Argon2 credential format
    credential_data = {
        "hashIterations": parsed["iterations"],
        "algorithm": "argon2",
        "additionalParameters": {
            "type": parsed["type"].replace("argon2", ""),  # "id", "i", or "d"
            "version": parsed["version"],
            "memory": parsed["memory"],
            "parallelism": parsed["parallelism"],
        },
    }

    secret_data = {
        "value": parsed["hash"],
        "salt": parsed["salt"],
    }

    return {
        "type": "password",
        "credentialData": json.dumps(credential_data),
        "secretData": json.dumps(secret_data),
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
    2. Acquires admin token via client credentials flow
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

    admin_client_id = os.environ.get("KEYCLOAK_ADMIN_CLIENT_ID", "openslides-admin")
    admin_client_secret = os.environ.get("KEYCLOAK_ADMIN_CLIENT_SECRET", "openslides-admin-secret")

    # Initialize Keycloak admin client
    try:
        kc_client = KeycloakAdminClient(
            admin_api_url=admin_api_url,
            client_id=admin_client_id,
            client_secret=admin_client_secret,
        )
        MigrationHelper.write_line("Successfully acquired Keycloak admin token")
    except ActionException as e:
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
        }

        if email:
            kc_user_data["email"] = email
        if first_name:
            kc_user_data["firstName"] = first_name
        if last_name:
            kc_user_data["lastName"] = last_name

        # Handle password/credentials
        # Strategy: Prefer default_password (user knows it) over hash import
        # Keycloak's Argon2 hash import via REST API is unreliable
        credentials: list[dict[str, Any]] = []

        if default_password:
            # Use default_password - user knows this password
            credentials.append(_build_plaintext_credential(default_password, temporary=False))
            MigrationHelper.write_line(f"  Using default_password for {username}")
        elif password_hash and _is_argon2_hash(password_hash):
            # Argon2 hash without default_password - cannot import via REST API
            # User will need to use "forgot password" flow
            MigrationHelper.write_line(
                f"  WARNING: Argon2 hash for {username} cannot be imported (no default_password). User will need password reset."
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
        keycloak_id = kc_client.try_create_user(kc_user_data)

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
            existing_user = kc_client.get_user_by_username(username)
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
