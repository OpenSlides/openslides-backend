import io
from contextlib import redirect_stdout
from typing import Optional, Tuple

from datastore.migrations import MigrationException

from migrations import MigrationHandler, assert_migration_index

from ...action.action_handler import ActionHandler
from ...shared.exceptions import View400Exception
from ...shared.interfaces.wsgi import ResponseBody
from ..request import Request
from .base_view import BaseView, route


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
        handler = ActionHandler(logging=self.logging, services=self.services)
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
        handler = ActionHandler(logging=self.logging, services=self.services)
        response = handler.handle_request(request.json, -1, internal=True)
        self.logger.debug("Internal action request finished successfully.")
        return response, None

    @route("migrations", internal=True)
    def migrations_route(self, request: Request) -> Tuple[ResponseBody, Optional[str]]:
        self.logger.debug("Start executing migrations request.")

        if not (command := request.json.get("cmd")):
            raise View400Exception("No command provided")

        handler = MigrationHandler(request.json.get("verbose", False))

        f = io.StringIO()
        try:
            with redirect_stdout(f):
                handler.execute_command(command)
        except MigrationException as e:
            raise View400Exception(str(e))
        output = f.getvalue()

        self.logger.debug("Migrations request finished successfully.")
        return {
            "success": True,
            "output": output,
        }, None

    @route("health", method="GET", json=False)
    def health_route(self, request: Request) -> Tuple[ResponseBody, Optional[str]]:
        return {"status": "running"}, None
