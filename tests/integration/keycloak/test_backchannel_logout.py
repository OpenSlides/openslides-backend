"""
Integration tests for OIDC backchannel logout.

These tests verify that the backchannel logout endpoint correctly:
1. Validates incoming logout tokens
2. Invalidates sessions in the local cache
3. Publishes session invalidations to Redis

Requirements for live tests:
- Running Keycloak instance
- Running Redis instance
"""

import time
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from openslides_backend.http.views.base_view import (
    _invalidated_sessions,
    _sessions_lock,
    invalidate_session,
    is_session_invalidated,
)
from openslides_backend.shared.exceptions import PresenterException


class TestSessionInvalidationCache:
    """Tests for the session invalidation cache functions."""

    def setup_method(self) -> None:
        """Clear the session cache before each test."""
        with _sessions_lock:
            _invalidated_sessions.clear()

    def test_invalidate_session_adds_to_cache(self) -> None:
        """Test that invalidate_session adds session ID to cache."""
        session_id = f"test-session-{uuid.uuid4()}"

        invalidate_session(session_id)

        assert is_session_invalidated(session_id) is True

    def test_is_session_invalidated_returns_false_for_unknown(self) -> None:
        """Test that is_session_invalidated returns False for unknown sessions."""
        session_id = f"unknown-session-{uuid.uuid4()}"

        assert is_session_invalidated(session_id) is False

    def test_is_session_invalidated_prunes_old_entries(self) -> None:
        """Test that old entries are pruned from the cache."""
        old_session = f"old-session-{uuid.uuid4()}"
        new_session = f"new-session-{uuid.uuid4()}"

        # Add an old session with a timestamp in the past
        with _sessions_lock:
            _invalidated_sessions[old_session] = time.time() - 1000  # 1000 seconds ago

        # Add a new session
        invalidate_session(new_session)

        # Check - old session should be pruned, new should remain
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

    @pytest.fixture
    def mock_request(self) -> MagicMock:
        """Create a mock request object."""
        request = MagicMock()
        request.form = {}
        return request

    @pytest.fixture
    def mock_view(self) -> MagicMock:
        """Create a mock ActionView instance."""
        view = MagicMock()
        view.logger = MagicMock()
        return view

    def setup_method(self) -> None:
        """Clear the session cache before each test."""
        with _sessions_lock:
            _invalidated_sessions.clear()

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

        mock_redis_instance = MagicMock()
        mock_redis_class = MagicMock(return_value=mock_redis_instance)

        with patch(
            "openslides_backend.shared.oidc_validator.get_oidc_validator",
            return_value=mock_validator,
        ):
            with patch(
                "openslides_backend.http.views.action_view.redis.Redis",
                mock_redis_class,
            ):
                result, _ = ActionView.oidc_backchannel_logout(view, request)

        assert result == {"status": "ok"}
        assert is_session_invalidated(session_id) is True
        mock_redis_instance.xadd.assert_called_once_with("logout", {"sessionId": session_id})

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


class TestBackchannelLogoutIntegration:
    """
    Integration tests that require a running Keycloak instance.

    These tests verify the full backchannel logout flow including:
    - Keycloak sending logout tokens
    - Session invalidation affecting subsequent requests
    """

    @pytest.fixture
    def keycloak_available(self) -> bool:
        """Check if Keycloak is available."""
        try:
            from .keycloak_test_helper import KeycloakTestHelper

            helper = KeycloakTestHelper()
            helper._get_admin_token()
            return True
        except Exception:
            return False

    @pytest.fixture
    def keycloak_helper(self) -> Any:
        """Provide Keycloak test helper."""
        from .keycloak_test_helper import KeycloakTestHelper

        return KeycloakTestHelper()

    @pytest.mark.skipif(
        "not config.getoption('--keycloak', default=False)",
        reason="Keycloak integration tests disabled",
    )
    def test_logout_from_keycloak_invalidates_session(
        self, keycloak_helper: Any
    ) -> None:
        """
        Test that logging out a user from Keycloak invalidates their session.

        This test:
        1. Creates a user in Keycloak
        2. Authenticates the user to get a session
        3. Logs out the user via Keycloak Admin API
        4. Verifies the session is invalidated

        Note: This requires Keycloak to be configured with backchannel logout
        pointing to the backend's /system/auth/oidc-backchannel-logout endpoint.
        """
        # This test is a placeholder for when we have full E2E testing
        # The actual implementation would require:
        # 1. A user with an active session
        # 2. Triggering logout via Keycloak Admin API
        # 3. Keycloak sending the backchannel logout request
        # 4. Verifying the session is rejected on subsequent requests
        pytest.skip("Full E2E backchannel logout test not yet implemented")
