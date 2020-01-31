import logging
import os
from typing import Any, Type

from dependency_injector import containers, providers  # type: ignore
from gunicorn.app.base import BaseApplication  # type: ignore

from .environment import get_environment
from .http.application import OpenSlidesBackendWSGIApplication
from .http.views import ActionsView, RestrictionsView
from .services.authentication import AuthenticationHTTPAdapter
from .services.database import DatabaseHTTPAdapter
from .services.event_store import EventStoreHTTPAdapter
from .services.permission import PermissionHTTPAdapter
from .shared.interfaces import View, WSGIApplication

# ATTENTION: We use the Python builtin logging module. To change it use
# something like "import custom_logging as logging".


class OpenSlidesBackendServices(containers.DeclarativeContainer):
    """
    Services required by OpenSlidesBackendWSGIApplication.
    """

    config = providers.Configuration("config")
    logging = providers.Object(0)
    authentication = providers.Singleton(
        AuthenticationHTTPAdapter, config.authentication_url, logging
    )
    permission = providers.Singleton(PermissionHTTPAdapter, config.permission_url)
    database = providers.Singleton(DatabaseHTTPAdapter, config.database_url, logging)
    event_store = providers.Singleton(EventStoreHTTPAdapter, config.event_store_url)


class OpenSlidesBackendWSGI(containers.DeclarativeContainer):
    """
    Container for dependency injection into OpenSlidesBackendWSGIApplication.
    """

    logging = providers.Object(0)

    view = providers.Object(0)

    services = providers.DependenciesContainer()

    setup = providers.Factory(
        OpenSlidesBackendWSGIApplication, logging=logging, view=view, services=services,
    )


def create_wsgi_application(view_name: str) -> WSGIApplication:
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
    if view_name == "ActionsView":
        view = ActionsView
    else:
        # view_name == "RestrictionsView"
        view = RestrictionsView

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

    # Create WSGI application instance. Inject logging module, view class and services container.
    application_factory = OpenSlidesBackendWSGI(
        logging=logging, view=view, services=services
    )
    application = application_factory.setup()

    return application


class OpenSlidesBackendGunicornApplication(BaseApplication):  # pragma: no cover
    """
    Standalone application class for Gunicorn. It prepares Gunicorn for using
    OpenSlidesBackendWSGIApplication via OpenSlidesBackendWSGIContainer either
    with actions (sub)service or with restrictions (sub)service.
    """

    def __init__(self, view_name: str, *args: Any, **kwargs: Any) -> None:
        # Setup global loglevel.
        if os.environ.get("OPENSLIDES_BACKEND_DEBUG"):
            logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        self.view_name = view_name
        if self.view_name not in ("ActionsView", "RestrictionsView"):
            raise RuntimeError(
                f"View name has to be ActionsView or RestrictionsView, not {self.view_name}."
            )
        logger.debug(f"Create gunicorn application for {self.view_name}.")
        super().__init__(*args, **kwargs)

    def load_config(self) -> None:
        loglevel = "debug" if os.environ.get("OPENSLIDES_BACKEND_DEBUG") else "info"
        options = {
            "bind": "0.0.0.0:8000",
            "worker_tmp_dir": "/dev/shm",  # See https://pythonspeed.com/articles/gunicorn-in-docker/
            "timeout": int(os.environ.get("OPENSLIDES_BACKEND_WORKER_TIMEOUT", "30")),
            "loglevel": loglevel,
            "reload": loglevel == "debug",
        }
        for key, value in options.items():
            self.cfg.set(key, value)

    def load(self) -> WSGIApplication:
        return create_wsgi_application(self.view_name)


def start_actions_server() -> None:  # pragma: no cover
    OpenSlidesBackendGunicornApplication(view_name="ActionsView").run()


def start_restictions_server() -> None:  # pragma: no cover
    OpenSlidesBackendGunicornApplication(view_name="RestrictionsView").run()


def main() -> None:  # pragma: no cover
    start_actions_server()
    # start_restictions_server()
