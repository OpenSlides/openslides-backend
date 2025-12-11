from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from unittest.mock import _patch, patch

from osauthlib import ANONYMOUS_USER, AuthHandler

from openslides_backend.services.auth.adapter import AuthenticationHTTPAdapter
from openslides_backend.shared.exceptions import AuthenticationException
from openslides_backend.shared.interfaces.event import Event
from openslides_backend.shared.interfaces.logging import LoggingModule
from openslides_backend.shared.patterns import collection_and_id_from_fqid, id_from_fqid

from .util import Client


# Method(s) from Client
def login(self: Any, username: str, password: str, user_id: int) -> None:
    if self.application.services.authentication().is_anonymous(user_id):
        self.update_auth_data(
            {
                "access_token": "",
                "refresh_id": "",
            }
        )
    else:
        if (
            (user := self.auth.user_sessions.get(user_id))
            and user.get("username") == username
            and user.get("password") == password
        ):
            self.update_auth_data(
                {
                    "access_token": (
                        access_token := MockAuthenticationHTTPAdapter._create_auth_token(
                            user_id
                        )
                    ),
                    "refresh_id": (
                        refresh_id := MockAuthenticationHTTPAdapter._create_cookie_header(
                            user_id
                        )
                    ),
                }
            )
            self.auth.auth_token_to_user_ids[access_token] = user_id
            self.auth.cookie_to_user_ids[refresh_id] = user_id
        else:
            raise AuthenticationException(
                f"Mock: Wrong credentials for user {user_id}:{username}:{password}"
            )


class MockAuthenticationHTTPAdapter:
    """
    Adapter to connect to authentication service.
    """

    user_sessions: dict[int, dict[str, str]]
    auth_token_to_user_ids: dict[str, int]
    cookie_to_user_ids: dict[str, int]

    @staticmethod
    def _create_auth_token(user_id: int) -> str:
        return f"mocked auth token/{user_id}"

    @staticmethod
    def _create_cookie_header(user_id: int) -> str:
        return f"mocked cookie header user_id/{user_id}"

    def __init__(self, logging: LoggingModule) -> None:
        self.logger = logging.getLogger(__name__)
        self.auth_handler = AuthHandler(self.logger.debug)
        self.headers = {"Content-Type": "application/json"}
        self.user_sessions = {}
        self.auth_token_to_user_ids = {}
        self.cookie_to_user_ids = {}
        self.access_token = ""
        self.refresh_id = ""

    def authenticate(self) -> tuple[int, str | None]:
        self.logger.debug(
            f"Mock: Start request to authentication service with the following data: access_token: {self.access_token}, cookie: {self.refresh_id}"
        )
        if not self.access_token or not self.refresh_id:
            return ANONYMOUS_USER, None
        if user_id := self.auth_token_to_user_ids.get(self.access_token):
            return user_id, self.access_token
        elif (user_id := id_from_fqid(self.access_token)) in self.user_sessions:
            self.auth_token_to_user_ids[self.access_token] = user_id
            return user_id, self.access_token
        message = f"Mock: Auth error on auth_token {self.access_token}"
        self.logger.debug(f"Error in auth service: {message}")
        raise AuthenticationException(message)

    def hash(self, toHash: str) -> str:
        return toHash

    def is_equal(self, toHash: str, toCompare: str) -> bool:
        return toHash == toCompare

    def create_authorization_token(self, user_id: int, email: str) -> str:
        if user_id in self.user_sessions:
            token = MockAuthenticationHTTPAdapter._create_auth_token(user_id)
            self.user_sessions[user_id]["token"] = token
            self.user_sessions[user_id]["email"] = email
            self.auth_token_to_user_ids[token] = user_id
            return token
        raise AuthenticationException(
            f"mock: on creation authorization_token user:{user_id} email: {email}"
        )

    def verify_authorization_token(self, user_id: int, token: str) -> bool:
        if found_user_id := self.auth_token_to_user_ids.get(token):
            return user_id == found_user_id
        raise AuthenticationException(f"mock user:{user_id}: Failed to verify token.")

    def clear_all_sessions(self) -> None:
        self.auth_token_to_user_ids.pop(self.access_token, None)
        self.cookie_to_user_ids.pop(self.refresh_id, None)
        try:
            user_id = id_from_fqid(self.access_token)
        except IndexError:
            user_id = None
        if user_id:
            self.user_sessions.pop(user_id, None)

    def create_update_user_session(self, event: Event) -> None:
        collection, user_id = collection_and_id_from_fqid(event["fqid"])
        if collection == "user":
            if event.get("type") == "create":
                self.user_sessions[user_id] = event.get("fields", {})
            elif event.get("type") == "update":
                self.user_sessions[user_id].update(event.get("fields", {}))


login_patch = patch.object(Client, "login", new=login)
auth_http_adapter_patch = patch.multiple(
    AuthenticationHTTPAdapter,
    spec=True,
    **{
        method_name: getattr(MockAuthenticationHTTPAdapter, method_name)
        for method_name in dir(MockAuthenticationHTTPAdapter)
        if not method_name.startswith("_") or method_name == "__init__"
    },
)
AuthenticationHTTPAdapter.create_update_user_session = (  # type: ignore
    MockAuthenticationHTTPAdapter.create_update_user_session
)


@contextmanager
def auth_mock() -> Generator[tuple[_patch, _patch], None, None]:
    with auth_http_adapter_patch:
        with login_patch:
            yield auth_http_adapter_patch, login_patch
