from typing import Any, Dict, List

from ..actions import Actions
from ..actions.actions import ActionsHandler
from ..actions.actions import Payload as ActionsPayload
from ..presenter import Payload as PresenterPayload
from ..presenter import Presenter
from ..presenter.presenter import PresenterHandler
from ..restrictions import Payload as RestrictionsPayload
from ..restrictions import RestrictionResponse, Restrictions
from ..restrictions.restrictions import RestrictionsHandler
from ..shared.exceptions import (
    ActionException,
    AuthenticationException,
    PermissionDenied,
    PresenterException,
    RestrictionException,
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


class ActionsView(BaseView):
    """
    The ActionsView receives a bundle of actions via HTTP and handles it to the
    ActionsHandler after retrieving request user id.
    """

    method = "POST"

    def dispatch(self, body: RequestBody, headers: Headers) -> ResponseBody:
        """
        Dispatches request to the viewpoint.
        """
        self.logger.debug("Start dispatching actions request.")

        # Get request user id.
        try:
            self.user_id = self.services.authentication().get_user(headers)
        except AuthenticationException as exception:
            raise ViewException(exception.message, status_code=400)

        # Setup payload
        payload: ActionsPayload = body

        # Handle request.
        handler: Actions = ActionsHandler()
        try:
            result = handler.handle_request(
                payload, self.user_id, self.logging, self.services
            )
        except ActionException as exception:
            raise ViewException(exception.message, status_code=400)
        except PermissionDenied as exception:
            raise ViewException(exception.message, status_code=403)

        self.logger.debug("Action request finished successfully.")
        return result


class RestrictionsView(BaseView):
    """
    The RestrictionsView receives a bundle of restrictions via HTTP and handles
    it to the RestrictionsHandler.
    """

    method = "GET"

    def dispatch(self, body: RequestBody, headers: Headers) -> ResponseBody:
        """
        Dispatches request to the viewpoint.
        """
        self.logger.debug("Start dispatching restrictions request.")

        # Setup payload
        payload: RestrictionsPayload = body

        # Handle request.
        handler: Restrictions = RestrictionsHandler()
        try:
            restriction_response = handler.handle_request(
                payload, self.logging, self.services
            )
        except RestrictionException as exception:
            raise ViewException(exception.message, status_code=400)
        response = self.parse_restriction_response(restriction_response)
        self.logger.debug(
            "Restrictions request finished successfully. Send response now."
        )
        return response

    def parse_restriction_response(
        self, restriction_response: RestrictionResponse
    ) -> List[Dict[str, Any]]:
        result = []
        for blob in restriction_response:
            blob_result = {}
            for fqfield, value in blob.items():
                blob_result[str(fqfield)] = value
            result.append(blob_result)
        return result


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

        # Setup payload
        payload: PresenterPayload = body

        # Handle request.
        handler: Presenter = PresenterHandler()
        try:
            presenter_response = handler.handle_request(
                payload, self.logging, self.services
            )
        except PresenterException as exception:
            raise ViewException(exception.message, status_code=400)
        self.logger.debug("Presenter request finished successfully. Send response now.")
        return presenter_response
