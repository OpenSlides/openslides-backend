from typing import Optional, Tuple

from ...presenter.presenter import PresenterHandler
from ...shared.interfaces.wsgi import ResponseBody
from ..request import Request
from .base_view import BaseView, route


class PresenterView(BaseView):
    """
    The PresenterView receives a bundle of presentations via HTTP and handles
    it to the PresenterHandler.
    """

    method = "POST"

    @route("handle_request")
    def presenter_route(self, request: Request) -> Tuple[ResponseBody, Optional[str]]:
        self.logger.debug("Start dispatching presenter request.")

        # Handle request.
        handler = PresenterHandler(
            logging=self.logging,
            services=self.services,
        )
        presenter_response, access_token = handler.handle_request(request)

        # Finish request.
        self.logger.debug("Presenter request finished successfully. Send response now.")
        return presenter_response, access_token

    @route("health", internal=True, method="GET", json=False)
    def health_route(self, request: Request) -> Tuple[ResponseBody, Optional[str]]:
        return {"status": "unkown"}, None
