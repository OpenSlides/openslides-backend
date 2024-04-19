import logging
import multiprocessing
import os
import signal
import sys
import time
from typing import Any

from gunicorn.app.base import BaseApplication

from openslides_backend.datastore.reader.services import register_services

from .action.action_worker import gunicorn_post_request, gunicorn_worker_abort
from .shared.env import Environment
from .shared.interfaces.logging import LoggingModule
from .shared.interfaces.wsgi import WSGIApplication

register_services()

# ATTENTION: We use the Python builtin logging module. To change this use
# something like "import custom_logging as logging".

DEFAULT_ADDRESSES = {
    "ActionView": "0.0.0.0:9002",
    "PresenterView": "0.0.0.0:9003",
}


class OpenSlidesBackendGunicornApplication(BaseApplication):  # pragma: no cover
    """
    Standalone application class for Gunicorn. It prepares Gunicorn for using
    OpenSlidesBackendWSGIApplication via OpenSlidesBackendWSGIContainer either
    with action component or with presenter component.
    """

    def __init__(
        self, view_name: str, env: Environment, *args: Any, **kwargs: Any
    ) -> None:
        self.env = env

        logging.basicConfig(level=self.env.get_loglevel())
        logger = logging.getLogger(__name__)

        self.view_name = view_name
        if self.view_name not in ("ActionView", "PresenterView"):
            raise ValueError(
                f"View name has to be ActionView or PresenterView, not {self.view_name}."
            )
        logger.debug(f"Create gunicorn application for {self.view_name}.")
        logger.debug(f"Using environment: {self.env.vars}")

        super().__init__(*args, **kwargs)

    def load_config(self) -> None:
        options = {
            "bind": self.env.get_address(self.view_name),
            "workers": int(self.env.OPENSLIDES_BACKEND_NUM_WORKERS),
            "worker_tmp_dir": "/dev/shm",  # See https://pythonspeed.com/articles/gunicorn-in-docker/
            "timeout": int(self.env.OPENSLIDES_BACKEND_WORKER_TIMEOUT),
            "graceful_timeout": 30,  # time to finish after receiving restart signal
            "loglevel": self.env.get_loglevel().lower(),
            "reload": self.env.is_dev_mode(),
            "reload_engine": "auto",  # This is the default however.
            "worker_class": "gthread",  # async gthread with unlimited prolongation possibility
            "threads": int(
                self.env.OPENSLIDES_BACKEND_NUM_THREADS
            ),  # Threads per Worker(process)
            "post_request": gunicorn_post_request,
            "worker_abort": gunicorn_worker_abort,
        }
        for key, value in options.items():
            self.cfg.set(key, value)

    def load(self) -> WSGIApplication:
        # We import this here so Gunicorn can use its reload feature properly.
        from .wsgi import create_wsgi_application

        # TODO: Fix this typing problem.
        logging_module: LoggingModule = logging  # type: ignore

        return create_wsgi_application(logging_module, self.view_name, self.env)


def start_action_server(env: Environment) -> None:  # pragma: no cover
    OpenSlidesBackendGunicornApplication(view_name="ActionView", env=env).run()


def start_presenter_server(env: Environment) -> None:  # pragma: no cover
    OpenSlidesBackendGunicornApplication(view_name="PresenterView", env=env).run()


def start_them_all(env: Environment) -> None:  # pragma: no cover
    print(
        f"Start all components in child processes. Parent process id is {os.getpid()}."
    )
    processes = {
        "action": multiprocessing.Process(target=start_action_server, args=(env,)),
        "presenter": multiprocessing.Process(
            target=start_presenter_server, args=(env,)
        ),
    }
    for process in processes.values():
        process.start()

    def sigterm_handler(signalnum: int, _: Any) -> None:
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
    env = Environment(os.environ)
    component = env.OPENSLIDES_BACKEND_COMPONENT
    if component == "action":
        start_action_server(env)
    elif component == "presenter":
        start_presenter_server(env)
    elif component == "all":
        if env.is_dev_mode():
            start_them_all(env)
            sys.exit(0)
        print(
            f"Error: OPENSLIDES_BACKEND_COMPONENT must not be {component} in production mode (see OPENSLIDES_DEVELOPMENT).",
            file=sys.stderr,
        )
        sys.stderr.flush()
        sys.exit(1)
    else:
        print(
            f"Error: OPENSLIDES_BACKEND_COMPONENT must not be {component}.",
            file=sys.stderr,
        )
        sys.stderr.flush()
        sys.exit(1)
    sys.exit(0)
