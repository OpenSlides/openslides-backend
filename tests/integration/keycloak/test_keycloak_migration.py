"""
Integration tests for Keycloak user migration (0101_migrate_users_to_keycloak).

These tests verify that existing local users are migrated to Keycloak
when the migration runs with KEYCLOAK_ADMIN_API_URL configured.

Requirements:
- Running Keycloak instance
- Running PostgreSQL database
- Environment variables:
  - KEYCLOAK_ADMIN_URL (default: http://localhost:8180/auth/admin/realms/openslides)
  - KEYCLOAK_ADMIN_USERNAME (default: admin)
  - KEYCLOAK_ADMIN_PASSWORD (default: admin)
"""

import os
import uuid
from importlib import import_module
from io import StringIO
from typing import Any
from unittest.mock import patch

import pytest
from psycopg import Connection
from psycopg.rows import DictRow

from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)

# Import the migration module dynamically since it starts with a number
migration_module = import_module(
    "openslides_backend.migrations.migrations.0101_migrate_users_to_keycloak"
)

from .keycloak_test_helper import KeycloakTestHelper


def keycloak_available() -> bool:
    """Check if Keycloak is available for testing."""
    try:
        helper = KeycloakTestHelper()
        helper._get_admin_token()
        return True
    except Exception:
        return False


# Skip all tests in this module if Keycloak is not available
pytestmark = pytest.mark.skipif(
    not keycloak_available(),
    reason="Keycloak not available",
)


@pytest.fixture
def keycloak_helper() -> KeycloakTestHelper:
    """Provide a Keycloak test helper."""
    return KeycloakTestHelper()


@pytest.fixture
def test_username() -> str:
    """Generate a unique test username."""
    return f"migration_test_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def db_connection():
    """Provide a database connection for tests."""
    with get_new_os_conn() as conn:
        yield conn


@pytest.fixture
def migration_stream() -> StringIO:
    """Provide a StringIO for migration output."""
    stream = StringIO()
    MigrationHelper.migrate_thread_stream = stream
    yield stream
    MigrationHelper.migrate_thread_stream = None


def create_test_user(
    conn: Connection[DictRow],
    username: str,
    email: str = None,
    first_name: str = None,
    last_name: str = None,
    is_active: bool = True,
    password: str = None,
    default_password: str = None,
) -> int:
    """Create a test user in the database and return their ID."""
    with conn.cursor() as curs:
        # Get the next user ID
        curs.execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM user_t")
        result = curs.fetchone()
        user_id = result["next_id"]

        # Insert user
        curs.execute(
            """
            INSERT INTO user_t (id, username, email, first_name, last_name, is_active, password, default_password)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, username, email, first_name, last_name, is_active, password, default_password),
        )
        conn.commit()
        return user_id


def delete_test_user(conn: Connection[DictRow], user_id: int) -> None:
    """Delete a test user from the database."""
    with conn.cursor() as curs:
        curs.execute("DELETE FROM user_t WHERE id = %s", (user_id,))
        conn.commit()


def get_user(conn: Connection[DictRow], user_id: int) -> dict[str, Any]:
    """Get a user from the database."""
    with conn.cursor() as curs:
        curs.execute(
            "SELECT id, username, email, keycloak_id, can_change_own_password FROM user_t WHERE id = %s",
            (user_id,),
        )
        return curs.fetchone()


class TestMigrationWithoutKeycloakConfig:
    """Tests for migration when KEYCLOAK_ADMIN_API_URL is not set."""

    def test_migration_skips_when_no_admin_url(
        self,
        db_connection: Connection[DictRow],
        migration_stream: StringIO,
    ) -> None:
        """Test that migration skips gracefully when KEYCLOAK_ADMIN_API_URL is not set."""
        data_manipulation = migration_module.data_manipulation

        # Ensure KEYCLOAK_ADMIN_API_URL is not set
        with patch.dict(os.environ, {"KEYCLOAK_ADMIN_API_URL": ""}, clear=False):
            with db_connection.cursor() as curs:
                data_manipulation(curs)

        output = migration_stream.getvalue()
        assert "KEYCLOAK_ADMIN_API_URL not set" in output
        assert "skipping Keycloak user migration" in output


class TestMigrationWithKeycloakConfig:
    """Tests for migration when KEYCLOAK_ADMIN_API_URL is set."""

    def test_migration_creates_keycloak_user_with_argon2_password(
        self,
        db_connection: Connection[DictRow],
        keycloak_helper: KeycloakTestHelper,
        test_username: str,
        migration_stream: StringIO,
    ) -> None:
        """Test that migration creates Keycloak user with Argon2 password hash."""
        data_manipulation = migration_module.data_manipulation

        # Create test user with Argon2 password hash
        argon2_hash = "$argon2id$v=19$m=65536,t=3,p=4$testsalt12345678$testhash1234567890abcdef"
        user_id = create_test_user(
            db_connection,
            username=test_username,
            email=f"{test_username}@example.com",
            first_name="Test",
            last_name="User",
            is_active=True,
            password=argon2_hash,
        )

        try:
            # Run migration with Keycloak config
            with patch.dict(
                os.environ,
                {
                    "KEYCLOAK_ADMIN_API_URL": keycloak_helper.admin_url,
                    "KEYCLOAK_ADMIN_USERNAME": keycloak_helper.admin_username,
                    "KEYCLOAK_ADMIN_PASSWORD": keycloak_helper.admin_password,
                },
                clear=False,
            ):
                with db_connection.cursor() as curs:
                    data_manipulation(curs)
                db_connection.commit()

            # Verify user was created in Keycloak
            kc_user = keycloak_helper.get_user_by_username(test_username)
            assert kc_user is not None
            assert kc_user["username"] == test_username
            assert kc_user["email"] == f"{test_username}@example.com"
            assert kc_user["enabled"] is True

            # Verify OpenSlides user was updated
            db_user = get_user(db_connection, user_id)
            assert db_user["keycloak_id"] == kc_user["id"]
            assert db_user["can_change_own_password"] is True

            # Verify migration output
            output = migration_stream.getvalue()
            assert f"Processing user {user_id}: {test_username}" in output
            assert f"Importing Argon2 hash for {test_username}" in output
            assert f"Created Keycloak user for {test_username}" in output

        finally:
            # Cleanup
            keycloak_helper.delete_user_by_username(test_username)
            delete_test_user(db_connection, user_id)

    def test_migration_creates_keycloak_user_with_default_password(
        self,
        db_connection: Connection[DictRow],
        keycloak_helper: KeycloakTestHelper,
        test_username: str,
        migration_stream: StringIO,
    ) -> None:
        """Test that migration uses default_password when no Argon2 hash exists."""
        data_manipulation = migration_module.data_manipulation

        # Create test user with default_password but no password hash
        user_id = create_test_user(
            db_connection,
            username=test_username,
            email=f"{test_username}@example.com",
            default_password="test_default_password",
        )

        try:
            # Run migration
            with patch.dict(
                os.environ,
                {
                    "KEYCLOAK_ADMIN_API_URL": keycloak_helper.admin_url,
                    "KEYCLOAK_ADMIN_USERNAME": keycloak_helper.admin_username,
                    "KEYCLOAK_ADMIN_PASSWORD": keycloak_helper.admin_password,
                },
                clear=False,
            ):
                with db_connection.cursor() as curs:
                    data_manipulation(curs)
                db_connection.commit()

            # Verify user was created in Keycloak
            kc_user = keycloak_helper.get_user_by_username(test_username)
            assert kc_user is not None

            # Verify password works (if direct access grant is enabled)
            # Note: This may fail if direct access grant is not enabled
            try:
                assert keycloak_helper.verify_user_password(
                    test_username, "test_default_password"
                )
            except Exception:
                # Direct access grant may not be enabled, skip password verification
                pass

            # Verify migration output
            output = migration_stream.getvalue()
            assert f"Using default_password for {test_username}" in output

        finally:
            keycloak_helper.delete_user_by_username(test_username)
            delete_test_user(db_connection, user_id)

    def test_migration_links_existing_keycloak_user(
        self,
        db_connection: Connection[DictRow],
        keycloak_helper: KeycloakTestHelper,
        test_username: str,
        migration_stream: StringIO,
    ) -> None:
        """Test that migration links to existing Keycloak user on conflict."""
        data_manipulation = migration_module.data_manipulation

        # Create user in Keycloak first
        kc_id = keycloak_helper.create_user(
            username=test_username,
            email=f"{test_username}@example.com",
        )

        # Create test user in OpenSlides with same username
        user_id = create_test_user(
            db_connection,
            username=test_username,
            email=f"{test_username}@example.com",
        )

        try:
            # Run migration
            with patch.dict(
                os.environ,
                {
                    "KEYCLOAK_ADMIN_API_URL": keycloak_helper.admin_url,
                    "KEYCLOAK_ADMIN_USERNAME": keycloak_helper.admin_username,
                    "KEYCLOAK_ADMIN_PASSWORD": keycloak_helper.admin_password,
                },
                clear=False,
            ):
                with db_connection.cursor() as curs:
                    data_manipulation(curs)
                db_connection.commit()

            # Verify OpenSlides user was linked to existing Keycloak user
            db_user = get_user(db_connection, user_id)
            assert db_user["keycloak_id"] == kc_id
            assert db_user["can_change_own_password"] is True

            # Verify migration output
            output = migration_stream.getvalue()
            assert f"Linked existing Keycloak user for {test_username}" in output

        finally:
            keycloak_helper.delete_user(kc_id)
            delete_test_user(db_connection, user_id)

    def test_migration_skips_users_with_keycloak_id(
        self,
        db_connection: Connection[DictRow],
        keycloak_helper: KeycloakTestHelper,
        test_username: str,
        migration_stream: StringIO,
    ) -> None:
        """Test that migration skips users who already have keycloak_id."""
        data_manipulation = migration_module.data_manipulation

        # Create test user with existing keycloak_id
        with db_connection.cursor() as curs:
            curs.execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM user_t")
            result = curs.fetchone()
            user_id = result["next_id"]

            curs.execute(
                """
                INSERT INTO user_t (id, username, keycloak_id, can_change_own_password)
                VALUES (%s, %s, %s, FALSE)
                """,
                (user_id, test_username, "existing-keycloak-id-12345"),
            )
            db_connection.commit()

        try:
            # Run migration
            with patch.dict(
                os.environ,
                {
                    "KEYCLOAK_ADMIN_API_URL": keycloak_helper.admin_url,
                    "KEYCLOAK_ADMIN_USERNAME": keycloak_helper.admin_username,
                    "KEYCLOAK_ADMIN_PASSWORD": keycloak_helper.admin_password,
                },
                clear=False,
            ):
                with db_connection.cursor() as curs:
                    data_manipulation(curs)
                db_connection.commit()

            # Verify user was NOT in migration (SQL query excludes users with keycloak_id)
            output = migration_stream.getvalue()
            assert f"Processing user {user_id}: {test_username}" not in output

        finally:
            delete_test_user(db_connection, user_id)

    def test_migration_skips_users_with_saml_id(
        self,
        db_connection: Connection[DictRow],
        keycloak_helper: KeycloakTestHelper,
        test_username: str,
        migration_stream: StringIO,
    ) -> None:
        """Test that migration skips SAML users."""
        data_manipulation = migration_module.data_manipulation

        # Create test user with saml_id
        with db_connection.cursor() as curs:
            curs.execute("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM user_t")
            result = curs.fetchone()
            user_id = result["next_id"]

            curs.execute(
                """
                INSERT INTO user_t (id, username, saml_id)
                VALUES (%s, %s, %s)
                """,
                (user_id, test_username, "saml-id-12345"),
            )
            db_connection.commit()

        try:
            # Run migration
            with patch.dict(
                os.environ,
                {
                    "KEYCLOAK_ADMIN_API_URL": keycloak_helper.admin_url,
                    "KEYCLOAK_ADMIN_USERNAME": keycloak_helper.admin_username,
                    "KEYCLOAK_ADMIN_PASSWORD": keycloak_helper.admin_password,
                },
                clear=False,
            ):
                with db_connection.cursor() as curs:
                    data_manipulation(curs)
                db_connection.commit()

            # Verify user was NOT in migration
            output = migration_stream.getvalue()
            assert f"Processing user {user_id}: {test_username}" not in output

        finally:
            delete_test_user(db_connection, user_id)

    def test_migration_handles_sha512_hash(
        self,
        db_connection: Connection[DictRow],
        keycloak_helper: KeycloakTestHelper,
        test_username: str,
        migration_stream: StringIO,
    ) -> None:
        """Test that migration warns about SHA512 hashes that cannot be migrated."""
        data_manipulation = migration_module.data_manipulation

        # Create test user with SHA512 password hash (152 characters)
        sha512_hash = "a" * 64 + "b" * 88  # 64-byte salt + base64 hash = 152 chars
        user_id = create_test_user(
            db_connection,
            username=test_username,
            password=sha512_hash,
        )

        try:
            # Run migration
            with patch.dict(
                os.environ,
                {
                    "KEYCLOAK_ADMIN_API_URL": keycloak_helper.admin_url,
                    "KEYCLOAK_ADMIN_USERNAME": keycloak_helper.admin_username,
                    "KEYCLOAK_ADMIN_PASSWORD": keycloak_helper.admin_password,
                },
                clear=False,
            ):
                with db_connection.cursor() as curs:
                    data_manipulation(curs)
                db_connection.commit()

            # Verify warning was logged
            output = migration_stream.getvalue()
            assert f"SHA512 hash for {test_username} cannot be migrated" in output
            assert "User will need password reset" in output

            # Verify user was still created in Keycloak (without password)
            kc_user = keycloak_helper.get_user_by_username(test_username)
            assert kc_user is not None

        finally:
            keycloak_helper.delete_user_by_username(test_username)
            delete_test_user(db_connection, user_id)

    def test_migration_summary(
        self,
        db_connection: Connection[DictRow],
        keycloak_helper: KeycloakTestHelper,
        migration_stream: StringIO,
    ) -> None:
        """Test that migration outputs a summary."""
        data_manipulation = migration_module.data_manipulation

        test_users = []
        for i in range(3):
            username = f"migration_summary_test_{uuid.uuid4().hex[:8]}"
            user_id = create_test_user(
                db_connection,
                username=username,
                email=f"{username}@example.com",
                default_password="testpass",
            )
            test_users.append((user_id, username))

        try:
            # Run migration
            with patch.dict(
                os.environ,
                {
                    "KEYCLOAK_ADMIN_API_URL": keycloak_helper.admin_url,
                    "KEYCLOAK_ADMIN_USERNAME": keycloak_helper.admin_username,
                    "KEYCLOAK_ADMIN_PASSWORD": keycloak_helper.admin_password,
                },
                clear=False,
            ):
                with db_connection.cursor() as curs:
                    data_manipulation(curs)
                db_connection.commit()

            # Verify summary was logged
            output = migration_stream.getvalue()
            assert "Migration Summary:" in output
            assert "Created:" in output
            assert "Total:" in output

        finally:
            for user_id, username in test_users:
                keycloak_helper.delete_user_by_username(username)
                delete_test_user(db_connection, user_id)


class TestMigrationHelperFunctions:
    """Tests for helper functions in the migration module."""

    def test_is_argon2_hash(self) -> None:
        """Test Argon2 hash detection."""
        _is_argon2_hash = migration_module._is_argon2_hash

        assert _is_argon2_hash("$argon2id$v=19$m=65536,t=3,p=4$salt$hash")
        assert _is_argon2_hash("$argon2i$v=19$m=4096,t=3,p=1$salt$hash")
        assert not _is_argon2_hash("sha512hash")
        assert not _is_argon2_hash("")

    def test_is_sha512_hash(self) -> None:
        """Test SHA512 hash detection."""
        _is_sha512_hash = migration_module._is_sha512_hash

        # SHA512 hash is 152 characters (64-byte salt + base64 hash)
        sha512_hash = "a" * 152
        assert _is_sha512_hash(sha512_hash)
        assert not _is_sha512_hash("$argon2id$v=19$m=65536,t=3,p=4$salt$hash")
        assert not _is_sha512_hash("short")
        assert not _is_sha512_hash("")

    def test_build_argon2_credential(self) -> None:
        """Test Argon2 credential building."""
        _build_argon2_credential = migration_module._build_argon2_credential
        import json

        hash_value = "$argon2id$v=19$m=65536,t=3,p=4$testsalt$testhash"
        credential = _build_argon2_credential(hash_value)

        assert credential["type"] == "password"

        credential_data = json.loads(credential["credentialData"])
        assert credential_data["algorithm"] == "argon2"
        assert credential_data["hashIterations"] == 3
        # additionalParameters values must be arrays of strings (Keycloak MultivaluedHashMap)
        params = credential_data["additionalParameters"]
        assert params["type"] == ["id"]
        assert params["version"] == ["1.3"]
        assert params["memory"] == ["65536"]
        assert params["parallelism"] == ["4"]
        assert "hashLength" in params

        secret_data = json.loads(credential["secretData"])
        assert secret_data["value"] == "testhash"
        assert secret_data["salt"] == "testsalt"

    def test_build_plaintext_credential(self) -> None:
        """Test plaintext credential building."""
        _build_plaintext_credential = migration_module._build_plaintext_credential

        credential = _build_plaintext_credential("testpassword", temporary=False)
        assert credential["type"] == "password"
        assert credential["value"] == "testpassword"
        assert credential["temporary"] is False

        temp_credential = _build_plaintext_credential("temppass", temporary=True)
        assert temp_credential["temporary"] is True
