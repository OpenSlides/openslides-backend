from ...migrations.migration_helper import MigrationHelper
from ...presenter.presenter import PresenterHandler
from ...services.postgresql.db_connection_handling import get_new_os_conn
from ...shared.interfaces.wsgi import RouteResponse
from ..request import Request
from .base_view import BaseView, route


class IDPView(BaseView):
    """
    The IDPView receives a logout token from a backchannel logout request originating
    from the IDP Service. Handled by an ActionHandler.
    This View just passes along the HTTP Request to the block_session_id action
    """

    method = "POST"

    @route("handle_request")
    def backchannel_logout_route(self, request: Request) -> RouteResponse:
        self.logger.debug("Received IDP backchannel logout request")

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                MigrationHelper.assert_migration_index(curs)

        # Execute user.block_session action
        # Request validation and blocklisting will be performed in the action
        handler = ActionHandler(self.env, self.services, self.logging)
        payload = [
            {
                "action": "user.block_session_id",
                "data": [{"request": request}],
            }
        ]

        response = handle_action_in_worker_thread(
            request.json, 0, True, handler, internal=True
        )

        return response, None
