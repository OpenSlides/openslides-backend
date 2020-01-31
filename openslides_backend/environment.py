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


def get_environment() -> Environment:
    """
    Parses environment variables and sets their defaults if they do not exist.
    """

    authentication_url = os.environ.get(
        "OPENSLIDES_BACKEND_AUTHENTICATION_URL", "http://localhost:9000/"
    )
    permission_url = os.environ.get(
        "OPENSLIDES_BACKEND_PERMISSION_URL", "http://localhost:9001/"
    )
    database_url = os.environ.get(
        "OPENSLIDES_BACKEND_DATABASE_URL", "http://localhost:9002/"
    )
    event_store_url = os.environ.get(
        "OPENSLIDES_BACKEND_EVENT_STORE_URL", "http://localhost:9003/"
    )

    return Environment(
        authentication_url=authentication_url,
        permission_url=permission_url,
        database_url=database_url,
        event_store_url=event_store_url,
    )
