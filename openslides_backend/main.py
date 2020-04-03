import logging
import multiprocessing
import os
import signal
import sys
import time
from typing import Any, Type

from dependency_injector import containers, providers  # type: ignore
from gunicorn.app.base import BaseApplication  # type: ignore

from .environment import get_environment
from .http.application import OpenSlidesBackendWSGIApplication
from .http.views import ActionsView, PresenterView, RestrictionsView
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
    elif view_name == "RestrictionsView":
        view = RestrictionsView
    else:
        # view_name == "PresenterView"
        view = PresenterView

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
    with actions component or with restrictions component or with presenter
    component.
    """

    ports = {
        "ActionsView": 8000,
        "RestrictionsView": 8001,
        "PresenterView": 8002,
    }

    def __init__(self, view_name: str, *args: Any, **kwargs: Any) -> None:
        # Setup global loglevel.
        if os.environ.get("OPENSLIDES_BACKEND_DEBUG"):
            logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        self.view_name = view_name
        if self.view_name not in ("ActionsView", "RestrictionsView", "PresenterView"):
            raise RuntimeError(
                f"View name has to be ActionsView or RestrictionsView or PresenterView, not {self.view_name}."
            )
        logger.debug(f"Create gunicorn application for {self.view_name}.")
        super().__init__(*args, **kwargs)

    def load_config(self) -> None:
        loglevel = "debug" if os.environ.get("OPENSLIDES_BACKEND_DEBUG") else "info"
        options = {
            "bind": f"0.0.0.0:{self.ports[self.view_name]}",
            "worker_tmp_dir": "/dev/shm",  # See https://pythonspeed.com/articles/gunicorn-in-docker/
            "timeout": int(os.environ.get("OPENSLIDES_BACKEND_WORKER_TIMEOUT", "30")),
            "loglevel": loglevel,
            # TODO: This does not work. Changes will reload the application, but code changed do not reflect.
            "reload": loglevel == "debug",
            "reload_engine": "auto",
        }
        for key, value in options.items():
            self.cfg.set(key, value)

    def load(self) -> WSGIApplication:
        return create_wsgi_application(self.view_name)


def start_actions_server() -> None:  # pragma: no cover
    OpenSlidesBackendGunicornApplication(view_name="ActionsView").run()


def start_restrictions_server() -> None:  # pragma: no cover
    OpenSlidesBackendGunicornApplication(view_name="RestrictionsView").run()


def start_presenter_server() -> None:  # pragma: no cover
    OpenSlidesBackendGunicornApplication(view_name="PresenterView").run()


def start_addendum_server() -> None:  # pragma: no cover
    # TODO: Start a permanent running process that listens to event stream and
    # pushes additional fqfields that might be new for some users.
    print("Start addendum server ...")
    while True:
        pass


def start_them_all() -> None:  # pragma: no cover
    print(
        f"Start all components in child processes. Parent process id is {os.getpid()}."
    )
    processes = {
        "actions": multiprocessing.Process(target=start_actions_server),
        "restrictions": multiprocessing.Process(target=start_restrictions_server),
        "presenter": multiprocessing.Process(target=start_presenter_server),
        "addendum": multiprocessing.Process(target=start_addendum_server),
    }
    for process in processes.values():
        process.start()

    def sigterm_handler(signalnum: int, current_stack_frame: Any) -> None:
        strsignal = signal.strsignal  # type: ignore
        print(
            f"Parent process {os.getpid()} received {strsignal(signalnum)} "
            "signal. Terminate all child processes first."
        )
        for child in multiprocessing.active_children():
            child.terminate()
            child.join()
        print(f"Parent process {os.getpid()} terminated successfully.")
        sys.exit(0)

    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    while True:
        for name, process in processes.items():
            if not process.is_alive():
                process.join()
                print(
                    f"Component {name} terminated. Terminate all other components now."
                )
                for other_name, other_process in processes.items():
                    if name != other_name:
                        other_process.terminate()
                        other_process.join()
                print("Parent process terminated.")
                sys.exit(1)
        time.sleep(0.1)


def main() -> None:  # pragma: no cover
    component = os.environ.get("OPENSLIDES_BACKEND_COMPONENT", "all")
    if component == "actions":
        start_actions_server()
    elif component == "restrictions":
        start_restrictions_server()
    elif component == "presenter":
        start_presenter_server()
    elif component == "addendum":
        start_addendum_server()
    elif component == "all":
        start_them_all()
    else:
        print(
            f"Error: OPENSLIDES_BACKEND_COMPONENT must not be {component}.",
            file=sys.stderr,
        )
        sys.stderr.flush()
        sys.exit(1)
    sys.exit(0)
