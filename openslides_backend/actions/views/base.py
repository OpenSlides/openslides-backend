from ..adapters.authentication import AuthenticationHTTPAdapter
from ..adapters.database import DatabaseHTTPAdapter
from ..adapters.event_store import EventStoreHTTPAdapter
from ..adapters.permission import PermissionHTTPAdapter
from ..adapters.protocols import (
    AuthenticationAdapter,
    DatabaseAdapter,
    EventStoreAdapter,
    PermissionAdapter,
)
from ..general.environment import Environment
from .protocols import Request


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

    def dispatch(self, request: Request, **kwargs: dict) -> None:
        """
        Main entrypoint for a view.
        """
        raise NotImplementedError
