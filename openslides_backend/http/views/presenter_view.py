from ...migrations.migration_helper import MigrationHelper
from ...presenter.presenter import PresenterHandler
from ...services.postgresql.db_connection_handling import get_new_os_conn
from ...shared.interfaces.wsgi import RouteResponse
from ..request import Request
from .base_view import BaseView, route


class PresenterView(BaseView):
    """
    The PresenterView receives a bundle of presentations via HTTP and handles
    it to the PresenterHandler.
    """

    method = "POST"

    @route("handle_request")
    def presenter_route(self, request: Request) -> RouteResponse:
        self.logger.debug("Start dispatching presenter request.")

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                MigrationHelper.assert_migration_index(curs)

        # Get user id.
        user_id, access_token = self.get_user_id_from_headers(
            request.headers, request.cookies
        )

        # Handle request.
        handler = PresenterHandler(
            env=self.env,
            logging=self.logging,
            services=self.services,
        )
        presenter_response = handler.handle_request(request, user_id)

        # Finish request.
        self.logger.debug("Presenter request finished successfully. Send response now.")
        return presenter_response, access_token

    @route("health", method="GET", json=False)
    def health_route(self, request: Request) -> RouteResponse:
        return {"status": "running"}, None
