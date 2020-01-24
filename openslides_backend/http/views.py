from typing import Any, Callable, Dict, List, Optional, Type

from ..actions import Actions
from ..actions import Payload as ActionsPayload
from ..actions.actions import ActionsHandler
from ..restrictions import Payload as RestrictionsPayload
from ..restrictions import RestrictionResponse, Restrictions
from ..restrictions.restrictions import RestrictionsHandler
from ..shared.exceptions import (
    ActionException,
    AuthenticationException,
    PermissionDenied,
    RestrictionException,
    ViewException,
)
from ..shared.interfaces import Headers, LoggingModule, Services

# TODO Use proper type here.
RequestBody = Any
ResponseBody = Optional[List[Any]]


class View:
    """
    Base class for views of this service.

    During initialization we bind the dependencies to the instance.
    """

    def __init__(self, logging: LoggingModule, services: Services) -> None:
        self.services = services
        self.logging = logging
        self.logger = logging.getLogger(__name__)

    def dispatch(
        self, body: RequestBody, headers: Headers, **kwargs: dict
    ) -> ResponseBody:
        """
        Main entrypoint for a view.
        """
        raise NotImplementedError


view_map: Dict[str, Type[View]] = {}


def register_view(name: str) -> Callable[[Type[View]], Type[View]]:
    """
    Decorator to be used for view classes. Registers the class so that it can
    be found by the WSGI application.
    """

    def wrapper(view: Type[View]) -> Type[View]:
        view_map[name] = view
        return view

    return wrapper


@register_view("ActionView")
class ActionView(View):
    """
    The ActionView receives a bundle of actions via HTTP and handles it to the
    ActionsHandler after retrieving request user id.
    """

    def dispatch(
        self, body: RequestBody, headers: Headers, **kwargs: dict
    ) -> ResponseBody:
        """
        Dispatches request to the viewpoint.
        """
        self.logger.debug("Start dispatching actions request.")

        # Get request user id.
        try:
            self.user_id = self.services.authentication().get_user(headers)
        except AuthenticationException as exception:
            raise ViewException(exception.message)

        # Setup payload
        payload: ActionsPayload = body

        # Handle request.
        handler: Actions = ActionsHandler()
        try:
            handler.handle_request(payload, self.user_id, self.logging, self.services)
        except ActionException as exception:
            raise ViewException(exception.message)
        except PermissionDenied:  # TODO: Do not use different exceptions here.
            raise

        self.logger.debug("Action request finished successfully.")
        return None


@register_view("RestrictionView")
class RestrictionView(View):
    """
    The RestrictionView receives a bundle of restrictions via HTTP and handles
    it to the RestrictionsHandler.
    """

    def dispatch(
        self, body: RequestBody, headers: Headers, **kwargs: dict
    ) -> ResponseBody:
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
            raise ViewException(exception.message)
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
