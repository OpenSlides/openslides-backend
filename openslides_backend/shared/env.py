from enum import Enum, auto
from typing import Any, Dict

DEV_PASSWORD = "openslides"


class Loglevel(Enum):
    NOTSET = auto()
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


def is_truthy(value: str) -> bool:
    truthy = ("1", "on", "true")
    return value.lower() in truthy


class Environment:
    """
    Contains all environment variables. See the vars attribute for all defaults.
    """

    vars = {
        "ACTION_PORT": "9002",
        "DATASTORE_READER_HOST": "localhost",
        "DATASTORE_READER_PATH": "/internal/datastore/reader",
        "DATASTORE_READER_PORT": "9010",
        "DATASTORE_READER_PROTOCOL": "http",
        "DATASTORE_WRITER_HOST": "localhost",
        "DATASTORE_WRITER_PATH": "/internal/datastore/writer",
        "DATASTORE_WRITER_PORT": "9011",
        "DATASTORE_WRITER_PROTOCOL": "http",
        "INTERNAL_AUTH_PASSWORD_FILE": "",
        "MEDIA_HOST": "localhost",
        "MEDIA_PATH": "/internal/media",
        "MEDIA_PORT": "9006",
        "MEDIA_PROTOCOL": "http",
        "OPENSLIDES_BACKEND_COMPONENT": "all",
        "OPENSLIDES_BACKEND_NUM_WORKERS": "1",
        "OPENSLIDES_BACKEND_NUM_THREADS": "3",
        "OPENSLIDES_BACKEND_RAISE_4XX": "false",
        "OPENSLIDES_BACKEND_WORKER_TIMEOUT": "30",
        "OPENSLIDES_BACKEND_THREAD_WATCH_TIMEOUT": "1",
        "OPENSLIDES_DEVELOPMENT": "false",
        "OPENSLIDES_LOGLEVEL": Loglevel.NOTSET.name,
        "OPENTELEMETRY_ENABLED": "false",
        "PRESENTER_PORT": "9003",
        "VOTE_HOST": "vote",
        "VOTE_PATH": "/internal/vote",
        "VOTE_PORT": "9013",
        "VOTE_PROTOCOL": "http",
    }

    def __init__(self, os_env: Any, *args: Any, **kwargs: Any) -> None:
        for key in self.vars.keys():
            env = os_env.get(key)
            if env is not None:
                self.vars[key] = env

    def __getattr__(self, attr: str) -> str:
        value = self.vars.get(attr)
        if value is None:
            raise AttributeError(f"Environment variable {attr} not found")
        return value

    def is_dev_mode(self) -> bool:
        return is_truthy(self.OPENSLIDES_DEVELOPMENT)

    def is_otel_enabled(self) -> bool:
        return is_truthy(self.OPENTELEMETRY_ENABLED)

    def get_loglevel(self) -> str:
        lvl = self.OPENSLIDES_LOGLEVEL.upper()
        if lvl not in Loglevel.__members__:
            raise ValueError(f"Invalid OPENSLIDES_LOGLEVEL: {lvl}")
        if lvl == Loglevel.NOTSET.name:
            if self.is_dev_mode():
                return Loglevel.DEBUG.name
            return Loglevel.INFO.name
        return lvl

    def get_address(self, view: str) -> str:
        if view == "ActionView":
            return f"0.0.0.0:{self.ACTION_PORT}"
        elif view == "PresenterView":
            return f"0.0.0.0:{self.PRESENTER_PORT}"
        raise ValueError(f"Invalid view {view}")

    def get_service_url(self) -> Dict[str, str]:
        service_url = {}
        # Extend the vars attribute with the lower case properties for the service URLs.
        for service in ("datastore_reader", "datastore_writer", "media", "vote"):
            key = service + "_url"
            service_url[key] = self.get_endpoint(service.upper())
        return service_url

    def get_endpoint(self, service: str) -> str:
        parts = {}
        for suffix in ("PROTOCOL", "HOST", "PORT", "PATH"):
            name = "_".join((service, suffix))
            parts[suffix] = self.vars[name]
        return f"{parts['PROTOCOL']}://{parts['HOST']}:{parts['PORT']}{parts['PATH']}"
