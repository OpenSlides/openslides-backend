from typing import Type

from dependency_injector import containers, providers

from .environment import get_environment
from .http.application import OpenSlidesBackendWSGIApplication
from .http.views import ActionView, PresenterView
from .services.auth.adapter import AuthenticationHTTPAdapter
from .services.datastore.extended_adapter import ExtendedDatastoreAdapter
from .services.datastore.http_engine import HTTPEngine
from .services.media.adapter import MediaServiceAdapter
from .services.vote.adapter import VoteAdapter
from .shared.interfaces.logging import LoggingModule
from .shared.interfaces.wsgi import View, WSGIApplication


class OpenSlidesBackendServices(containers.DeclarativeContainer):
    """
    Services required by OpenSlidesBackendWSGIApplication.
    """

    config = providers.Configuration("config")
    logging = providers.Object(0)
    authentication = providers.Singleton(AuthenticationHTTPAdapter, logging)
    media = providers.Singleton(MediaServiceAdapter, config.media_url, logging)
    engine = providers.Singleton(
        HTTPEngine, config.datastore_reader_url, config.datastore_writer_url, logging
    )
    datastore = providers.Factory(ExtendedDatastoreAdapter, engine, logging)
    vote = providers.Singleton(VoteAdapter, config.vote_url, logging)


class OpenSlidesBackendWSGI(containers.DeclarativeContainer):
    """
    Container for dependency injection into OpenSlidesBackendWSGIApplication.
    """

    logging = providers.Object(0)

    view = providers.Object(0)

    services = providers.DependenciesContainer()

    setup = providers.Factory(
        OpenSlidesBackendWSGIApplication,
        logging=logging,
        view=view,
        services=services,
    )


def create_wsgi_application(logging: LoggingModule, view_name: str) -> WSGIApplication:
    """
    Application factory function to create a new instance of the WSGI
    application.

    Parses services configuration from environment variables and injects view
    class and dependencies.
    """
    # Get environment
    environment = get_environment()
    logging.getLogger(__name__).debug(f"Using environment: {environment}.")

    # Get view class
    view: Type[View]
    if view_name == "ActionView":
        view = ActionView
    elif view_name == "PresenterView":
        view = PresenterView
    else:
        raise ValueError(f"The value of view_name must not be {view_name}.")

    # Setup services
    services = OpenSlidesBackendServices(
        config=environment,
        logging=logging,
    )

    # Create WSGI application instance. Inject logging module, view class and services container.
    application_factory = OpenSlidesBackendWSGI(
        logging=logging, view=view, services=services
    )
    application = application_factory.setup()

    return application
