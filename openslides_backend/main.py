import logging
import multiprocessing
import os
import signal
import sys
import time
from typing import Any

from gunicorn.app.base import BaseApplication  # type: ignore

from .shared.interfaces import LoggingModule, WSGIApplication

# ATTENTION: We use the Python builtin logging module. To change this use
# something like "import custom_logging as logging".


class OpenSlidesBackendGunicornApplication(BaseApplication):  # pragma: no cover
    """
    Standalone application class for Gunicorn. It prepares Gunicorn for using
    OpenSlidesBackendWSGIApplication via OpenSlidesBackendWSGIContainer either
    with actions component or with presenter component.
    """

    ports = {
        "ActionsView": 8000,  # TODO: Don not hard code this.
        "PresenterView": 8001,
    }

    def __init__(self, view_name: str, *args: Any, **kwargs: Any) -> None:
        # Setup global loglevel.
        if os.environ.get("OPENSLIDES_BACKEND_DEBUG"):
            logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        self.view_name = view_name
        if self.view_name not in ("ActionsView", "PresenterView"):
            raise ValueError(
                f"View name has to be ActionsView or PresenterView, not {self.view_name}."
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
            "reload_engine": "auto",  # This is the default however.
        }
        for key, value in options.items():
            self.cfg.set(key, value)

    def load(self) -> WSGIApplication:
        # We import this here so Gunicorn can use its reload feature properly.
        from .wsgi import create_wsgi_application

        # TODO: Fix this typing problem.
        logging_module: LoggingModule = logging  # type: ignore

        return create_wsgi_application(logging_module, self.view_name)


def start_actions_server() -> None:  # pragma: no cover
    OpenSlidesBackendGunicornApplication(view_name="ActionsView").run()


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
