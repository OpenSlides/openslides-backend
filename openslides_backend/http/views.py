from typing import Callable, Dict, Type

from .. import logging
from ..actions import Actions, Payload
from ..actions.actions import ActionsHandler
from ..services.authentication import AuthenticationHTTPAdapter
from ..services.database import DatabaseHTTPAdapter
from ..services.event_store import EventStoreHTTPAdapter
from ..services.permission import PermissionHTTPAdapter
from ..shared.exceptions import (
    ActionException,
    AuthenticationException,
    PermissionDenied,
    ViewException,
)
from ..shared.interfaces import (
    AuthenticationAdapter,
    DatabaseAdapter,
    EventStoreAdapter,
    Headers,
    PermissionAdapter,
)
from .environment import Environment

logger = logging.getLogger(__name__)


class View:
    """
    Base class for view of this service.

    During initialization we bind the services to the instance.
    """

    def __init__(self, environment: Environment) -> None:
        self.authentication_adapter: AuthenticationAdapter = AuthenticationHTTPAdapter(
            environment["authentication_url"]
        )
        self.permission_adapter: PermissionAdapter = PermissionHTTPAdapter(
            environment["permission_url"]
        )
        self.database_adapter: DatabaseAdapter = DatabaseHTTPAdapter(
            environment["database_url"]
        )
        self.event_store_adapter: EventStoreAdapter = EventStoreHTTPAdapter(
            environment["event_store_url"]
        )

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
    def dispatch(self, payload: Payload, headers: Headers, **kwargs: dict) -> None:
        """
        Dispatches request to the viewpoint.
        """
        logger.debug("Start dispatching action request.")

        # Get request user id
        try:
            self.user_id = self.authentication_adapter.get_user(headers)
        except AuthenticationException as exception:
            raise ViewException(exception.message)

        services = {
            "permission_adapter": self.permission_adapter,
            "database_adapter": self.database_adapter,
            "event_store_adapter": self.event_store_adapter,
        }
        handler: Actions = ActionsHandler()
        try:
            handler.handle_request(payload, self.user_id, services)
        except ActionException as exception:
            raise ViewException(exception.message)
        except PermissionDenied:  # TODO: Do not use different exceptions here.
            raise
