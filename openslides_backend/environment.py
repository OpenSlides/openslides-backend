import os

from mypy_extensions import TypedDict

Environment = TypedDict(
    "Environment",
    {
        "authentication_url": str,
        "permission_url": str,
        "datastore_reader_url": str,
        "datastore_writer_url": str,
    },
)

DEFAULT_PROTOCOL = "http"
DEFAULT_HOST = "localhost"
DEFAULT_AUTHENTICATION_PORT = 9000
DEFAULT_PERMISSION_PORT = 9001
DEFAULT_DATASTORE_READER_PORT = 9002
DEFAULT_DATASTORE_WRITER_PORT = 9002


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
    datastore_reader_url = (
        get_url_from_env(
            "OPENSLIDES_BACKEND_DATASTORE_READER_URL",
            get_fallback_url(DEFAULT_HOST, DEFAULT_DATASTORE_READER_PORT),
        )
        + "/internal/datastore/reader"
    )
    datastore_writer_url = (
        get_url_from_env(
            "OPENSLIDES_BACKEND_DATASTORE_WRITER_URL",
            get_fallback_url(DEFAULT_HOST, DEFAULT_DATASTORE_WRITER_PORT),
        )
        + "/internal/datastore/writer"
    )

    return Environment(
        authentication_url=authentication_url,
        permission_url=permission_url,
        datastore_reader_url=datastore_reader_url,
        datastore_writer_url=datastore_writer_url,
    )


def get_url_from_env(env: str, fallback: str) -> str:
    return os.environ.get(env, fallback)


def get_fallback_url(host: str, port: int) -> str:
    """
    Helper function to build URL from given host and port.
    """
    return f"{DEFAULT_PROTOCOL}://{host}:{port}"
