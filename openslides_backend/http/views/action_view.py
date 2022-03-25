from base64 import b64decode
from typing import Optional, Tuple

from ...action.action_handler import ActionHandler
from ...migration_handler import assert_migration_index
from ...migration_handler.migration_handler import MigrationHandler
from ...shared.env import DEV_PASSWORD
from ...shared.exceptions import ServerError
from ...shared.interfaces.wsgi import ResponseBody
from ..http_exceptions import Unauthorized
from ..request import Request
from .base_view import BaseView, route

INTERNAL_AUTHORIZATION_HEADER = "Authorization"


class ActionView(BaseView):
    """
    The ActionView receives a bundle of actions via HTTP and handles it to the
    ActionHandler after retrieving request user id.
    """

    @route(["handle_request", "handle_separately"])
    def action_route(self, request: Request) -> Tuple[ResponseBody, Optional[str]]:
        self.logger.debug("Start dispatching action request.")

        assert_migration_index()

        # Get user id.
        user_id, access_token = self.get_user_id_from_headers(
            request.headers, request.cookies
        )
        # Set Headers and Cookies in services.
        self.services.vote().set_authentication(request.headers, request.cookies)

        # Handle request.
        handler = ActionHandler(self.env, self.services, self.logging)
        is_atomic = not request.environ["RAW_URI"].endswith("handle_separately")
        response = handler.handle_request(request.json, user_id, is_atomic)

        self.logger.debug("Action request finished successfully.")
        return response, access_token

    @route("handle_request", internal=True)
    def internal_action_route(
        self, request: Request
    ) -> Tuple[ResponseBody, Optional[str]]:
        self.logger.debug("Start dispatching internal action request.")

        assert_migration_index()
        self.check_internal_auth_password(request)

        handler = ActionHandler(self.env, self.services, self.logging)
        response = handler.handle_request(request.json, -1, internal=True)
        self.logger.debug("Internal action request finished successfully.")
        return response, None

    @route("migrations", internal=True)
    def migrations_route(self, request: Request) -> Tuple[ResponseBody, Optional[str]]:
        self.logger.debug("Start executing migrations request.")
        self.check_internal_auth_password(request)
        handler = MigrationHandler(self.env, self.services, self.logging)
        response = handler.handle_request(request.json)
        self.logger.debug("Migrations request finished successfully.")
        return {"success": True, **response}, None

    @route("health", method="GET", json=False)
    def health_route(self, request: Request) -> Tuple[ResponseBody, Optional[str]]:
        return {"status": "running"}, None

    def check_internal_auth_password(self, request: Request) -> None:
        request_password = request.headers.get(INTERNAL_AUTHORIZATION_HEADER)
        if self.env.is_dev_mode():
            secret_password = DEV_PASSWORD
        else:
            filename = self.env.INTERNAL_AUTH_PASSWORD_FILE
            if not filename:
                raise ServerError("Missing INTERNAL_AUTH_PASSWORD_FILE.")
            with open(filename) as file_:
                secret_password = file_.read()
        if (
            request_password is None
            or b64decode(request_password).decode() != secret_password
        ):
            raise Unauthorized()
