from typing import Any, Dict, Optional, Tuple

from ..action.action_handler import ActionHandler
from ..action.util.typing import Payload as ActionPayload
from ..presenter import Payload as PresenterPayload
from ..presenter.presenter import PresenterHandler
from ..shared.interfaces.logging import LoggingModule
from ..shared.interfaces.services import Services
from ..shared.interfaces.wsgi import Headers, RequestBody, ResponseBody, View


class BaseView(View):
    """
    Base class for views of this service.

    During initialization we bind the dependencies to the instance.
    """

    def __init__(self, logging: LoggingModule, services: Services) -> None:
        self.services = services
        self.logging = logging
        self.logger = logging.getLogger(__name__)

    def get_user_id_from_headers(
        self, headers: Headers, cookies: Dict
    ) -> Tuple[int, Optional[str]]:
        """
        Returns user id from authentication service using HTTP headers.
        """
        user_id, access_token = self.services.authentication().authenticate(
            headers, cookies
        )
        self.logger.debug(f"User id is {user_id}.")
        return user_id, access_token

    def dispatch(
        self, body: RequestBody, headers: Headers, cookies: Dict
    ) -> Tuple[ResponseBody, Optional[str]]:
        raise NotImplementedError()


class ActionView(BaseView):
    """
    The ActionView receives a bundle of actions via HTTP and handles it to the
    ActionHandler after retrieving request user id.
    """

    method = "POST"

    def dispatch(
        self, body: RequestBody, headers: Headers, cookies: Dict
    ) -> Tuple[ResponseBody, Optional[str]]:
        """
        Dispatches request to the viewpoint.
        """
        self.logger.debug("Start dispatching action request.")

        # Get user id.
        user_id, access_token = self.get_user_id_from_headers(headers, cookies)

        # Setup payload.
        payload: ActionPayload = body

        # Handle request.
        handler = ActionHandler(logging=self.logging, services=self.services)
        response = handler.handle_request(payload, user_id)

        self.logger.debug("Action request finished successfully.")
        return response, access_token

    def get_health_info(self) -> Dict[str, Any]:
        """
        Returns some status information. HTTP method is ignored.
        """
        return dict(actions=dict(ActionHandler.get_health_info()))


class PresenterView(BaseView):
    """
    The PresenterView receives a bundle of presentations via HTTP and handles
    it to the PresenterHandler.
    """

    method = "POST"

    def dispatch(
        self, body: RequestBody, headers: Headers, cookies: Dict
    ) -> Tuple[ResponseBody, Optional[str]]:
        """
        Dispatches request to the viewpoint.
        """
        self.logger.debug("Start dispatching presenter request.")

        # Get user_id.
        user_id, access_token = self.get_user_id_from_headers(headers, cookies)

        # Setup payload.
        payload: PresenterPayload = body

        # Handle request.
        handler = PresenterHandler(
            logging=self.logging,
            services=self.services,
        )
        presenter_response = handler.handle_request(payload, user_id)

        # Finish request.
        self.logger.debug("Presenter request finished successfully. Send response now.")
        return presenter_response, access_token

    def get_health_info(self) -> Dict[str, Any]:
        """
        Returns some status information. HTTP method is ignored.
        """
        return {"status": "unkown"}
