from typing import Callable, Dict, Type

from ..actions import Actions, Payload
from ..actions.actions import ActionsHandler
from ..shared.exceptions import (
    ActionException,
    AuthenticationException,
    PermissionDenied,
    ViewException,
)
from ..shared.interfaces import Headers, LoggingModule, Services


class View:
    """
    Base class for views of this service.

    During initialization we bind the dependencies to the instance.
    """

    def __init__(self, logging: LoggingModule, services: Services) -> None:
        self.services = services
        self.logging = logging
        self.logger = logging.getLogger(__name__)

    def dispatch(self, payload: Payload, headers: Headers, **kwargs: dict) -> None:
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

    def dispatch(self, payload: Payload, headers: Headers, **kwargs: dict) -> None:
        """
        Dispatches request to the viewpoint.
        """
        self.logger.debug("Start dispatching action request.")

        # Get request user id.
        try:
            self.user_id = self.services.authentication().get_user(headers)
        except AuthenticationException as exception:
            raise ViewException(exception.message)

        # Handle request.
        handler: Actions = ActionsHandler()
        try:
            handler.handle_request(payload, self.user_id, self.logging, self.services)
        except ActionException as exception:
            raise ViewException(exception.message)
        except PermissionDenied:  # TODO: Do not use different exceptions here.
            raise

        self.logger.debug("Action request finished successfully.")
