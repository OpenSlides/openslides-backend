from ...migrations import assert_migration_index
from ...presenter.presenter import PresenterHandler
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

        assert_migration_index()

        # Handle request.
        handler = PresenterHandler(
            env=self.env,
            logging=self.logging,
            services=self.services,
        )
        presenter_response, access_token = handler.handle_request(request)

        # Finish request.
        self.logger.debug("Presenter request finished successfully. Send response now.")
        return presenter_response, access_token

    @route("health", method="GET", json=False)
    def health_route(self, request: Request) -> RouteResponse:
        return {"status": "running"}, None
