import os

from mypy_extensions import TypedDict

Environment = TypedDict(
    "Environment",
    {
        "authentication_url": str,
        "permission_url": str,
        "database_url": str,
        "event_store_url": str,
        "worker_timeout": int,
    },
)


def get_environment() -> Environment:
    """
    Parses environment variables and sets their defaults if they do not exist.
    """

    authentication_url = (
        permission_url
    ) = database_url = event_store_url = os.environ.get(
        "OPENSLIDES_BACKEND_DATA_STORE_URL",
        "http://localhost:9000/",  # TODO: Use correct variables here.
    )
    worker_timeout = int(os.environ.get("OPENSLIDES_BACKEND_WORKER_TIMEOUT", "30"))
    return Environment(
        authentication_url=authentication_url,
        permission_url=permission_url,
        database_url=database_url,
        event_store_url=event_store_url,
        worker_timeout=worker_timeout,
    )
