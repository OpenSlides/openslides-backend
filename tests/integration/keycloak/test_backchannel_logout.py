"""
Integration tests for keycloak backchannel logout.

These tests verify that the backchannel logout endpoint correctly:
1. Validates incoming logout tokens
2. Invalidates sessions in Redis
3. Publishes session invalidations to Redis stream

Requirements for live tests:
- Running Keycloak instance
- Running Redis instance
"""

import os
import time
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import redis as redis_lib

from openslides_backend.http.views.base_view import (
    invalidate_session,
    is_session_invalidated,
)
from openslides_backend.shared.exceptions import PresenterException

from .keycloak_test_helper import KeycloakTestHelper


def _get_test_redis() -> redis_lib.Redis:
    """Get Redis client for test cleanup."""
    host = os.environ.get("MESSAGE_BUS_HOST", "localhost")
    port = int(os.environ.get("MESSAGE_BUS_PORT", "6379"))
    return redis_lib.Redis(host=host, port=port)


def _clear_session_cache() -> None:
    """Clear all invalidated session entries from Redis."""
    r = _get_test_redis()
    for key in r.scan_iter("invalidated_session:*"):
        r.delete(key)
    r.delete("invalidated_sessions")


class TestSessionInvalidationCache:
    """Tests for the session invalidation cache functions."""

    def setup_method(self) -> None:
        """Clear the session cache before each test."""
        _clear_session_cache()

    def test_invalidate_session_adds_to_cache(self) -> None:
        """Test that invalidate_session adds session ID to cache."""
        session_id = f"test-session-{uuid.uuid4()}"

        invalidate_session(session_id)

        assert is_session_invalidated(session_id) is True

    def test_is_session_invalidated_returns_false_for_unknown(self) -> None:
        """Test that is_session_invalidated returns False for unknown sessions."""
        session_id = f"unknown-session-{uuid.uuid4()}"

        assert is_session_invalidated(session_id) is False

    def test_is_session_invalidated_expires_old_entries(self) -> None:
        """Test that old entries expire via Redis TTL."""
        old_session = f"old-session-{uuid.uuid4()}"
        new_session = f"new-session-{uuid.uuid4()}"

        # Add an old session with a 1-second TTL directly via Redis
        r = _get_test_redis()
        r.setex(f"invalidated_session:{old_session}", 1, "1")

        # Add a new session normally
        invalidate_session(new_session)

        # Wait for old session to expire
        time.sleep(2)

        # Old session should have expired, new should remain
        assert is_session_invalidated(old_session) is False
        assert is_session_invalidated(new_session) is True

    def test_multiple_sessions_can_be_invalidated(self) -> None:
        """Test that multiple sessions can be tracked."""
        session1 = f"session-1-{uuid.uuid4()}"
        session2 = f"session-2-{uuid.uuid4()}"
        session3 = f"session-3-{uuid.uuid4()}"

        invalidate_session(session1)
        invalidate_session(session2)

        assert is_session_invalidated(session1) is True
        assert is_session_invalidated(session2) is True
        assert is_session_invalidated(session3) is False


class TestBackchannelLogoutEndpoint:
    """Tests for the backchannel logout endpoint."""

    def setup_method(self) -> None:
        """Clear the session cache before each test."""
        _clear_session_cache()

    def test_missing_logout_token_raises_400(self) -> None:
        """Test that missing logout_token returns 400 error."""
        from openslides_backend.http.views.action_view import ActionView
        from openslides_backend.shared.exceptions import View400Exception

        view = MagicMock(spec=ActionView)
        view.logger = MagicMock()

        request = MagicMock()
        request.form = {}  # No logout_token

        # Call the actual method
        with pytest.raises(View400Exception, match="Missing logout_token"):
            ActionView.oidc_backchannel_logout(view, request)

    def test_oidc_not_configured_raises_400(self) -> None:
        """Test that unconfigured OIDC returns 400 error."""
        from openslides_backend.http.views.action_view import ActionView
        from openslides_backend.shared.exceptions import View400Exception

        view = MagicMock(spec=ActionView)
        view.logger = MagicMock()

        request = MagicMock()
        request.form = {"logout_token": "some-token"}

        with patch(
            "openslides_backend.shared.oidc_validator.get_oidc_validator",
            return_value=None,
        ):
            with pytest.raises(View400Exception, match="OIDC not configured"):
                ActionView.oidc_backchannel_logout(view, request)

    def test_valid_logout_token_invalidates_session(self) -> None:
        """Test that a valid logout token invalidates the session."""
        from openslides_backend.http.views.action_view import ActionView

        view = MagicMock(spec=ActionView)
        view.logger = MagicMock()

        session_id = f"test-session-{uuid.uuid4()}"
        request = MagicMock()
        request.form = {"logout_token": "valid-token"}

        mock_validator = MagicMock()
        mock_validator.validate_logout_token.return_value = {
            "sid": session_id,
            "sub": "user-123",
            "events": {"http://schemas.openid.net/event/backchannel-logout": {}},
        }

        with patch(
            "openslides_backend.shared.oidc_validator.get_oidc_validator",
            return_value=mock_validator,
        ):
            result, _ = ActionView.oidc_backchannel_logout(view, request)

        assert result == {"status": "ok"}
        assert is_session_invalidated(session_id) is True

        # Verify Redis stream entry
        r = _get_test_redis()
        entries = r.xrevrange("logout", count=10)
        found = any(
            entry[1].get(b"sessionId") == session_id.encode()
            for entry in entries
        )
        assert found

    def test_invalid_logout_token_raises_exception(self) -> None:
        """Test that an invalid logout token raises an exception."""
        from openslides_backend.http.views.action_view import ActionView

        view = MagicMock(spec=ActionView)
        view.logger = MagicMock()

        request = MagicMock()
        request.form = {"logout_token": "invalid-token"}

        mock_validator = MagicMock()
        mock_validator.validate_logout_token.side_effect = PresenterException(
            "Invalid logout token signature"
        )

        with patch(
            "openslides_backend.shared.oidc_validator.get_oidc_validator",
            return_value=mock_validator,
        ):
            with pytest.raises(PresenterException, match="Invalid logout token"):
                ActionView.oidc_backchannel_logout(view, request)


class TestOidcValidatorLogoutToken:
    """Tests for the OIDC validator logout token validation."""

    def test_validate_logout_token_missing_event_raises(self) -> None:
        """Test that missing backchannel-logout event raises exception."""
        from openslides_backend.shared.oidc_validator import OidcTokenValidator

        # Create a mock token without the backchannel-logout event
        mock_payload = {
            "sid": "session-123",
            "sub": "user-123",
            "events": {},  # Missing backchannel-logout event
        }

        mock_key = MagicMock()
        mock_key.key = "test-key"

        mock_jwks_client = MagicMock()
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_key

        with patch(
            "openslides_backend.shared.oidc_validator.PyJWKClient",
            return_value=mock_jwks_client,
        ):
            validator = OidcTokenValidator(
                provider_url="https://keycloak.example.com/auth/realms/test",
                client_id="test-client",
            )
            # Force jwks_client initialization
            _ = validator.jwks_client

            with patch(
                "openslides_backend.shared.oidc_validator.jwt.decode",
                return_value=mock_payload,
            ):
                with pytest.raises(
                    PresenterException, match="missing backchannel-logout event"
                ):
                    validator.validate_logout_token("test-token")

    def test_validate_logout_token_missing_sid_raises(self) -> None:
        """Test that missing sid claim raises exception."""
        from openslides_backend.shared.oidc_validator import OidcTokenValidator

        # Create a mock token without sid
        mock_payload = {
            "sub": "user-123",
            "events": {"http://schemas.openid.net/event/backchannel-logout": {}},
            # Missing "sid"
        }

        mock_key = MagicMock()
        mock_key.key = "test-key"

        mock_jwks_client = MagicMock()
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_key

        with patch(
            "openslides_backend.shared.oidc_validator.PyJWKClient",
            return_value=mock_jwks_client,
        ):
            validator = OidcTokenValidator(
                provider_url="https://keycloak.example.com/auth/realms/test",
                client_id="test-client",
            )
            # Force jwks_client initialization
            _ = validator.jwks_client

            with patch(
                "openslides_backend.shared.oidc_validator.jwt.decode",
                return_value=mock_payload,
            ):
                with pytest.raises(PresenterException, match="Missing 'sid' claim"):
                    validator.validate_logout_token("test-token")

    def test_validate_logout_token_success(self) -> None:
        """Test successful logout token validation."""
        from openslides_backend.shared.oidc_validator import OidcTokenValidator

        session_id = f"session-{uuid.uuid4()}"
        mock_payload = {
            "sid": session_id,
            "sub": "user-123",
            "events": {"http://schemas.openid.net/event/backchannel-logout": {}},
            "aud": "test-client",
            "iss": "https://keycloak.example.com/auth/realms/test",
        }

        mock_key = MagicMock()
        mock_key.key = "test-key"

        mock_jwks_client = MagicMock()
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_key

        with patch(
            "openslides_backend.shared.oidc_validator.PyJWKClient",
            return_value=mock_jwks_client,
        ):
            validator = OidcTokenValidator(
                provider_url="https://keycloak.example.com/auth/realms/test",
                client_id="test-client",
            )
            # Force jwks_client initialization
            _ = validator.jwks_client

            with patch(
                "openslides_backend.shared.oidc_validator.jwt.decode",
                return_value=mock_payload,
            ):
                result = validator.validate_logout_token("test-token")

        assert result["sid"] == session_id
        assert "events" in result


def keycloak_available() -> bool:
    """Check if Keycloak is available for testing."""
    try:
        KeycloakTestHelper()._get_admin_token()
        return True
    except Exception:
        return False


def redis_available() -> bool:
    """Check if Redis is available for testing."""
    try:
        host = os.environ.get("MESSAGE_BUS_HOST", "localhost")
        port = int(os.environ.get("MESSAGE_BUS_PORT", "6379"))
        return redis_lib.Redis(host=host, port=port).ping()
    except Exception:
        return False


class TestBackchannelLogoutIntegration:
    """
    Integration tests for the backchannel logout flow against live services.

    Tests real JWKS validation, real session IDs, real Redis streams,
    and real Admin API session management.
    """

    pytestmark = pytest.mark.skipif(
        not keycloak_available(),
        reason="Keycloak not available",
    )

    @pytest.fixture
    def keycloak_helper(self) -> KeycloakTestHelper:
        return KeycloakTestHelper()

    @pytest.fixture
    def test_user(self, keycloak_helper: KeycloakTestHelper) -> Any:
        """Create a temporary Keycloak user for testing, delete after use."""
        username = f"bclogout_test_{uuid.uuid4().hex[:8]}"
        password = f"Pass-{uuid.uuid4().hex[:12]}"
        keycloak_id = keycloak_helper.create_user(
            username=username, password=password, enabled=True
        )
        user_info = {
            "username": username,
            "password": password,
            "keycloak_id": keycloak_id,
        }
        try:
            yield user_info
        finally:
            try:
                keycloak_helper.delete_user(keycloak_id)
            except Exception:
                pass

    @pytest.fixture
    def redis_client(self) -> Any:
        """Connect to Redis, skip if unavailable."""
        host = os.environ.get("MESSAGE_BUS_HOST", "localhost")
        port = int(os.environ.get("MESSAGE_BUS_PORT", "6379"))
        client = redis_lib.Redis(host=host, port=port)
        try:
            client.ping()
        except Exception:
            pytest.skip("Redis not available")
        return client

    @pytest.fixture
    def oidc_validator(self) -> Any:
        """Create a real OidcTokenValidator pointing to local Keycloak."""
        from openslides_backend.shared.oidc_validator import OidcTokenValidator

        provider_url = os.environ.get(
            "OIDC_PROVIDER_URL",
            "http://localhost:8180/auth/realms/openslides",
        )
        internal_provider_url = os.environ.get(
            "OIDC_INTERNAL_PROVIDER_URL",
            provider_url,
        )
        return OidcTokenValidator(
            provider_url=provider_url,
            client_id="openslides-client",
            client_secret="openslides-secret",
            internal_provider_url=internal_provider_url,
        )

    def test_real_token_has_sid_claim(
        self,
        keycloak_helper: KeycloakTestHelper,
        test_user: dict[str, str],
        oidc_validator: Any,
    ) -> None:
        """Authenticate a user and verify the access token contains a sid claim."""
        token_response = keycloak_helper.authenticate_user(
            test_user["username"], test_user["password"]
        )
        access_token = token_response["access_token"]

        payload = oidc_validator.validate_token(access_token)

        assert "sid" in payload, "Access token should contain 'sid' claim"
        assert isinstance(payload["sid"], str)
        assert len(payload["sid"]) > 0

    def test_session_invalidation_with_real_sid(
        self,
        keycloak_helper: KeycloakTestHelper,
        test_user: dict[str, str],
        oidc_validator: Any,
    ) -> None:
        """Get a real sid from Keycloak and test local session invalidation."""
        _clear_session_cache()

        token_response = keycloak_helper.authenticate_user(
            test_user["username"], test_user["password"]
        )
        payload = oidc_validator.validate_token(token_response["access_token"])
        real_sid = payload["sid"]

        invalidate_session(real_sid)

        assert is_session_invalidated(real_sid) is True
        assert is_session_invalidated(f"fake-sid-{uuid.uuid4()}") is False

    def test_redis_logout_stream_publish_and_read(
        self, redis_client: Any
    ) -> None:
        """Publish a session ID to the Redis logout stream and read it back."""
        test_sid = f"test-sid-{uuid.uuid4()}"

        redis_client.xadd("logout", {"sessionId": test_sid})

        entries = redis_client.xrevrange("logout", count=10)
        found = any(
            entry[1].get(b"sessionId") == test_sid.encode()
            for entry in entries
        )
        assert found, f"Session ID {test_sid} not found in Redis logout stream"

    def test_full_invalidation_flow(
        self,
        keycloak_helper: KeycloakTestHelper,
        test_user: dict[str, str],
        oidc_validator: Any,
        redis_client: Any,
    ) -> None:
        """End-to-end: authenticate, validate, invalidate locally, publish to Redis."""
        _clear_session_cache()

        token_response = keycloak_helper.authenticate_user(
            test_user["username"], test_user["password"]
        )
        payload = oidc_validator.validate_token(token_response["access_token"])
        real_sid = payload["sid"]

        # Invalidate locally
        invalidate_session(real_sid)

        # Publish to Redis (same as action_view does)
        redis_client.xadd("logout", {"sessionId": real_sid})

        # Verify local cache
        assert is_session_invalidated(real_sid) is True

        # Verify Redis stream
        entries = redis_client.xrevrange("logout", count=10)
        found = any(
            entry[1].get(b"sessionId") == real_sid.encode()
            for entry in entries
        )
        assert found, f"Session ID {real_sid} not found in Redis logout stream"

    def test_keycloak_admin_clears_user_sessions(
        self,
        keycloak_helper: KeycloakTestHelper,
        test_user: dict[str, str],
    ) -> None:
        """
        Create a session via authentication, then clear it via Admin API.

        This tests the Admin API trigger mechanism which in production causes
        Keycloak to send backchannel logout tokens.
        """
        keycloak_id = test_user["keycloak_id"]

        # Authenticate to create a Keycloak session
        keycloak_helper.authenticate_user(
            test_user["username"], test_user["password"]
        )

        # Verify session exists
        sessions = keycloak_helper.get_user_sessions(keycloak_id)
        assert len(sessions) > 0, "User should have at least one active session"

        # Logout via Admin API (triggers backchannel logout in production)
        keycloak_helper._make_request("POST", f"users/{keycloak_id}/logout")

        # Verify sessions are cleared
        sessions_after = keycloak_helper.get_user_sessions(keycloak_id)
        assert len(sessions_after) == 0, "User sessions should be cleared after admin logout"
