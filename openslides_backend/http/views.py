from typing import Any, Dict

from ..action import Action
from ..action.action import ActionHandler
from ..action.action import Payload as ActionPayload
from ..presenter import Payload as PresenterPayload
from ..presenter import Presenter
from ..presenter.presenter import PresenterHandler
from ..shared.exceptions import (
    ActionException,
    AuthenticationException,
    PermissionDenied,
    PresenterException,
    ViewException,
)
from ..shared.interfaces import (
    Headers,
    LoggingModule,
    RequestBody,
    ResponseBody,
    Services,
)


class BaseView:
    """
    Base class for views of this service.

    During initialization we bind the dependencies to the instance.
    """

    def __init__(self, logging: LoggingModule, services: Services) -> None:
        self.services = services
        self.logging = logging
        self.logger = logging.getLogger(__name__)

    def get_user_id_from_headers(self, headers: Headers) -> int:
        """
        Returns user id from authentication service using HTTP headers.
        """
        try:
            user_id = self.services.authentication().get_user(headers)
        except AuthenticationException as exception:
            raise ViewException(exception.message, status_code=400)
        self.logger.debug(f"User id is {user_id}.")
        return user_id


class ActionView(BaseView):
    """
    The ActionView receives a bundle of actions via HTTP and handles it to the
    ActionHandler after retrieving request user id.
    """

    method = "POST"

    def dispatch(self, body: RequestBody, headers: Headers) -> ResponseBody:
        """
        Dispatches request to the viewpoint.
        """
        self.logger.debug("Start dispatching action request.")

        # Get user id.
        user_id = self.get_user_id_from_headers(headers)

        # Setup payload.
        payload: ActionPayload = body

        # Handle request.
        handler: Action = ActionHandler(logging=self.logging, services=self.services)
        try:
            result = handler.handle_request(payload, user_id)
        except ActionException as exception:
            raise ViewException(exception.message, status_code=400)
        except PermissionDenied as exception:
            raise ViewException(exception.message, status_code=403)

        self.logger.debug("Action request finished successfully.")
        return result

    def get_health_info(self) -> Dict[str, Any]:
        """
        Returns some status information. HTTP method is ignored.
        """
        return {"actions": dict(ActionHandler.get_actions_dev_status())}


class PresenterView(BaseView):
    """
    The PresenterView receives a bundle of presentations via HTTP and handles
    it to the PresenterHandler.
    """

    method = "GET"

    def dispatch(self, body: RequestBody, headers: Headers) -> ResponseBody:
        """
        Dispatches request to the viewpoint.
        """
        self.logger.debug("Start dispatching presenter request.")

        # Get user_id.
        user_id = self.get_user_id_from_headers(headers)

        # Setup payload.
        payload: PresenterPayload = body

        # Handle request.
        handler = PresenterHandler(
            logging=self.logging, services=self.services,
        )
        try:
            presenter_response = handler.handle_request(payload, user_id)
        except PresenterException as exception:
            raise ViewException(exception.message, status_code=400)
        self.logger.debug("Presenter request finished successfully. Send response now.")
        return presenter_response

    def get_health_info(self) -> Dict[str, Any]:
        """
        Returns some status information. HTTP method is ignored.
        """
        return {"status": "unkown"}
