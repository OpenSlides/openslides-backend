import inspect
import os
import re
from collections.abc import Callable
from re import Pattern
from typing import Any, Optional

import redis
from osauthlib import AUTHENTICATION_HEADER, COOKIE_NAME
from werkzeug.exceptions import BadRequest as WerkzeugBadRequest

from ...shared.exceptions import View400Exception
from ...shared.interfaces.env import Env
from ...shared.interfaces.logging import LoggingModule
from ...shared.interfaces.services import Services
from ...shared.interfaces.wsgi import Headers, ResponseBody, RouteResponse, View
from ...shared.otel import make_span
from ..http_exceptions import MethodNotAllowed, NotFound
from ..request import Request

ROUTE_OPTIONS_ATTR = "__route_options"

_INVALIDATED_SESSIONS_KEY = "invalidated_sessions"
_SESSION_MAX_AGE = 900  # 15 minutes TTL for invalidated session entries

# Lazy Redis singleton for session checks
_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        host = os.environ.get("MESSAGE_BUS_HOST", "localhost")
        port = int(os.environ.get("MESSAGE_BUS_PORT", "6379"))
        _redis_client = redis.Redis(host=host, port=port)
    return _redis_client


def invalidate_session(session_id: str) -> None:
    """Add a session ID to the invalidated sessions set in Redis with TTL."""
    r = _get_redis()
    r.sadd(_INVALIDATED_SESSIONS_KEY, session_id)
    # Also set a per-key TTL entry so individual sessions expire
    r.setex(f"invalidated_session:{session_id}", _SESSION_MAX_AGE, "1")


def is_session_invalidated(session_id: str) -> bool:
    """Check if a session has been invalidated via backchannel logout (Redis)."""
    try:
        r = _get_redis()
        return bool(r.exists(f"invalidated_session:{session_id}"))
    except redis.RedisError:
        return False

RouteFunction = Callable[[Any, Request], tuple[ResponseBody, Optional[str]]]


def route(
    name: str | list[str],
    internal: bool = False,
    method: str = "POST",
    json: bool = True,
    prefix: str | None = None,
) -> Callable[[RouteFunction], RouteFunction]:
    route_options_list = []
    if isinstance(name, str):
        name = [name]
    for _name in name:
        route_parts: list[str] = [""]
        if internal:
            route_parts.append("internal")
        elif prefix is not None:
            # Use explicit prefix override
            route_parts.extend(["system", prefix])
        else:
            # extract the callers name to deduce the path's prefix
            frame = inspect.currentframe()
            assert frame and frame.f_back
            caller = inspect.getframeinfo(frame.f_back)[2]
            caller_prefix = caller.replace("View", "").lower()
            route_parts.extend(["system", caller_prefix])
        route_parts.append(_name.strip("/"))
        path = "/".join(route_parts)
        regex = re.compile("^" + path + "/?$")
        route_options = {
            "raw_path": path,
            "path": regex,
            "method": method,
            "json": json,
        }
        route_options_list.append(route_options)

    def wrapper(func: RouteFunction) -> RouteFunction:
        setattr(func, ROUTE_OPTIONS_ATTR, route_options_list)
        return func

    return wrapper


class BaseView(View):
    """
    Base class for views of this service.

    During initialization we bind the dependencies to the instance.
    """

    routes: dict[Pattern, Callable[[Request], RouteResponse]]

    def __init__(self, env: Env, logging: LoggingModule, services: Services) -> None:
        self.services = services
        self.env = env
        self.logging = logging
        self.logger = logging.getLogger(__name__)
        self.routes = {}

    def get_user_id_from_headers(
        self, headers: Headers, cookies: dict
    ) -> tuple[int, str | None]:
        """
        Returns user id from authentication service using HTTP headers.

        In OIDC mode, checks for Bearer token in Authorization or Authentication header
        and validates it via JWKS. Falls back to auth-service otherwise.
        """
        # Check for OIDC Bearer token (Authorization or Authentication header)
        # Traefik OIDC middleware may send either header
        auth_header = headers.get("Authorization", "") or headers.get("Authentication", "")
        if auth_header.lower().startswith("bearer "):
            from ...shared.oidc_validator import get_oidc_validator

            validator = get_oidc_validator()
            if validator:
                return self._authenticate_oidc(auth_header[7:], validator)

        # Fallback: Auth-Service
        self.services.authentication().set_authentication(
            headers.get(AUTHENTICATION_HEADER, ""), cookies.get(COOKIE_NAME, "")
        )
        user_id, access_token = self.services.authentication().authenticate()
        self.logger.debug(f"User id is {user_id}.")
        return user_id, access_token

    def _authenticate_oidc(
        self, token: str, validator: Any
    ) -> tuple[int, str | None]:
        """
        Validate OIDC token and return user_id.

        Looks up user by keycloak_id, provisioning if necessary.
        """
        from ...services.postgresql.db_connection_handling import get_new_os_conn
        from ...services.database.extended_database import ExtendedDatabase
        from ...shared.filters import FilterOperator

        # Store the Bearer token in authentication service so it's available
        # for downstream code (e.g., Keycloak Admin API calls)
        self.services.authentication().set_authentication(token, "")

        # 1. Token validieren
        payload = validator.validate_token(token)
        keycloak_id = payload.get("sub")
        if not keycloak_id:
            self.logger.error("Missing 'sub' claim in token")
            return 0, None

        # 1b. Check if session was invalidated via backchannel logout
        session_id = payload.get("sid")
        if session_id and is_session_invalidated(session_id):
            self.logger.debug(f"Session {session_id} invalidated via backchannel logout")
            return 0, None

        # 2. User lookup via keycloak_id
        with get_new_os_conn() as conn:
            datastore = ExtendedDatabase(conn, self.logging, self.env)
            users = datastore.filter(
                "user",
                FilterOperator("keycloak_id", "=", keycloak_id),
                ["id", "is_active"],
                lock_result=False,
            )

            if len(users) == 1:
                user = next(iter(users.values()))
                if not user.get("is_active", True):
                    self.logger.debug(f"User account is deactivated: {user.get('id')}")
                    return 0, None
                user_id = user["id"]
                self.logger.debug(f"OIDC user authenticated: {user_id}")
                return user_id, None
            elif len(users) > 1:
                self.logger.error(f"Multiple users found with keycloak_id: {keycloak_id}")
                return 0, None

        # 3. User not found - provision via userinfo endpoint
        self.logger.debug(f"User not found, provisioning for keycloak_id: {keycloak_id}")
        try:
            user_info = validator.get_user_info(token)
            user_id = self._provision_oidc_user(keycloak_id, user_info)
            if user_id:
                self.logger.debug(f"Provisioned new OIDC user: {user_id}")
                return user_id, None
        except Exception as e:
            self.logger.error(f"Failed to provision user: {e}")

        return 0, None

    def _provision_oidc_user(
        self, keycloak_id: str, user_info: dict[str, Any]
    ) -> int | None:
        """
        Provision a new user via the internal save_keycloak_account action.
        """
        from ...action.action_handler import ActionHandler

        # Prepare the action data from user_info
        action_data = {
            "keycloak_id": keycloak_id,
            "email": user_info.get("email"),
            "given_name": user_info.get("given_name"),
            "family_name": user_info.get("family_name"),
            "preferred_username": user_info.get("preferred_username"),
            "name": user_info.get("name"),
        }

        # Remove None values
        action_data = {k: v for k, v in action_data.items() if v is not None}

        handler = ActionHandler(self.env, self.services, self.logging)
        result = handler.handle_request(
            [{"action": "user.save_keycloak_account", "data": [action_data]}],
            user_id=-1,
            internal=True,
        )

        if result.get("success") and result.get("results"):
            action_results = result["results"]
            if action_results and action_results[0]:
                return action_results[0][0].get("user_id")

        return None

    def dispatch(self, request: Request) -> RouteResponse:
        functions = inspect.getmembers(
            self,
            predicate=lambda attr: inspect.ismethod(attr)
            and hasattr(attr, ROUTE_OPTIONS_ATTR),
        )
        with make_span(self.env, "base view"):
            for _, func in functions:
                route_options_list = getattr(func, ROUTE_OPTIONS_ATTR)
                for route_options in route_options_list:
                    if route_options["path"].match(request.environ["RAW_URI"]):
                        # Check request method
                        if request.method != route_options["method"]:
                            raise MethodNotAllowed(
                                valid_methods=[route_options["method"]]
                            )
                        self.logger.debug(f"Request method is {request.method}.")

                        if route_options["json"]:
                            # Check mimetype and parse JSON body. The result is cached in request.json
                            if not request.is_json:
                                raise View400Exception(
                                    "Wrong media type. Use 'Content-Type: application/json' instead."
                                )
                            try:
                                request_body = request.get_json()
                            except WerkzeugBadRequest as exception:
                                raise View400Exception(exception.description)
                            self.logger.debug(f"Request contains JSON: {request_body}.")

                        return func(request)
            raise NotFound()
