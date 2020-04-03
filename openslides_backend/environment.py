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

defualt_host = "localhost"
default_auth_port = 9000
default_perm_port = 9001
default_db_port = 9002
default_event_store_port = 9003


def get_environment() -> Environment:
    """
    Parses environment variables and sets their defaults if they do not exist.
    """

    authentication_url = get_url_from_env(
        "OPENSLIDES_BACKEND_AUTHENTICATION_URL",
        get_fallback_host(defualt_host, default_auth_port),
    )
    permission_url = get_url_from_env(
        "OPENSLIDES_BACKEND_PERMISSION_URL",
        get_fallback_host(defualt_host, default_perm_port),
    )
    database_url = get_url_from_env(
        "OPENSLIDES_BACKEND_DATABASE_URL",
        get_fallback_host(defualt_host, default_db_port),
    )
    event_store_url = get_url_from_env(
        "OPENSLIDES_BACKEND_EVENT_STORE_URL",
        get_fallback_host(defualt_host, default_event_store_port),
    )

    return Environment(
        authentication_url=authentication_url,
        permission_url=permission_url,
        database_url=database_url,
        event_store_url=event_store_url,
    )


def get_url_from_env(env: str, fallback: str) -> str:
    return os.environ.get(env, fallback)


def get_fallback_host(host: str, port: int) -> str:
    return f"https://{host}:{port}/"
