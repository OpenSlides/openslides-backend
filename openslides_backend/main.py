import logging
import os

from dependency_injector import containers, providers  # type: ignore

from .environment import get_environment
from .http.application import OpenSlidesBackendApplication
from .services.authentication import AuthenticationHTTPAdapter
from .services.database import DatabaseHTTPAdapter
from .services.event_store import EventStoreHTTPAdapter
from .services.permission import PermissionHTTPAdapter
from .shared.interfaces import Application


class OpenSlidesBackendServices(containers.DeclarativeContainer):
    """
    Services required by OpenSlidesBackendApplication.
    """

    config = providers.Configuration("config")
    logging = providers.Object(0)
    authentication = providers.Singleton(
        AuthenticationHTTPAdapter, config.authentication_url, logging
    )
    permission = providers.Singleton(PermissionHTTPAdapter, config.permission_url)
    database = providers.Singleton(DatabaseHTTPAdapter, config.database_url, logging)
    event_store = providers.Singleton(EventStoreHTTPAdapter, config.event_store_url)


class OpenSlidesBackend(containers.DeclarativeContainer):
    """
    Container for dependency injection into OpenSlidesBackendApplication.
    """

    logging = providers.Object(0)

    services = providers.DependenciesContainer()

    setup = providers.Factory(
        OpenSlidesBackendApplication, logging=logging, services=services,
    )


def create_application() -> Application:
    """
    Application factory function to create a new instance of the application.

    Parses services configuration from environment variables.
    """
    # Setup global loglevel.
    if os.environ.get("OPENSLIDES_BACKEND_DEBUG"):
        logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    logger.debug("Create application.")

    environment = get_environment()
    logger.debug(f"Using environment: {environment}.")

    # Setup services
    services = OpenSlidesBackendServices(
        config={
            "authentication_url": environment["authentication_url"],
            "permission_url": environment["permission_url"],
            "database_url": environment["database_url"],
            "event_store_url": environment["event_store_url"],
        },
        logging=logging,
    )

    # Create application instance. Inject logger and services.
    application_factory = OpenSlidesBackend(logging=logging, services=services)
    application = application_factory.setup()

    return application


application = create_application()
