import os

from mypy_extensions import TypedDict

Environment = TypedDict(
    "Environment",
    {
        "authentication_url": str,
        "permission_url": str,
        "database_url": str,
        "event_store_url": str,
    },
)

DEFAULT_PROTOCOL = "http"
DEFAULT_HOST = "localhost"
DEFAULT_AUTHENTICATION_PORT = 9000
DEFAULT_PERMISSION_PORT = 9001
DEFAULT_DATABASE_PORT = 9002
DEFAULT_EVENT_STORE_PORT = 9003


def get_environment() -> Environment:
    """
    Parses environment variables and sets their defaults if they do not exist.
    """

    authentication_url = get_url_from_env(
        "OPENSLIDES_BACKEND_AUTHENTICATION_URL",
        get_fallback_url(DEFAULT_HOST, DEFAULT_AUTHENTICATION_PORT),
    )
    permission_url = get_url_from_env(
        "OPENSLIDES_BACKEND_PERMISSION_URL",
        get_fallback_url(DEFAULT_HOST, DEFAULT_PERMISSION_PORT),
    )
    database_url = get_url_from_env(
        "OPENSLIDES_BACKEND_DATABASE_URL",
        get_fallback_url(DEFAULT_HOST, DEFAULT_DATABASE_PORT),
    )
    event_store_url = get_url_from_env(
        "OPENSLIDES_BACKEND_EVENT_STORE_URL",
        get_fallback_url(DEFAULT_HOST, DEFAULT_EVENT_STORE_PORT),
    )

    return Environment(
        authentication_url=authentication_url,
        permission_url=permission_url,
        database_url=database_url,
        event_store_url=event_store_url,
    )


def get_url_from_env(env: str, fallback: str) -> str:
    return os.environ.get(env, fallback)


def get_fallback_url(host: str, port: int) -> str:
    """
    Helper function to build URL from given host and port.
    """
    return f"{DEFAULT_PROTOCOL}://{host}:{port}/"
