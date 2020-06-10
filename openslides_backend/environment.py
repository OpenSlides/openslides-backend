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
DEFAULT_AUTHENTICATION_PORT = "9000"
DEFAULT_PERMISSION_PORT = "9001"
DEFAULT_DATASTORE_READER_PORT = "9002"
DEFAULT_DATASTORE_WRITER_PORT = "9002"


def get_environment() -> Environment:
    """
    Parses environment variables and sets their defaults if they do not exist.
    """
    authentication_endpoint = (
        DEFAULT_PROTOCOL
        + "://"
        + get_env("AUTHENTICATION_HOST", DEFAULT_HOST)
        + ":"
        + get_env("AUTHENTICATION_PORT", DEFAULT_AUTHENTICATION_PORT)
    )
    authentication_url = authentication_endpoint

    permission_endpoint = (
        DEFAULT_PROTOCOL
        + "://"
        + get_env("PERMISSION_HOST", DEFAULT_HOST)
        + ":"
        + get_env("PERMISSION_PORT", DEFAULT_PERMISSION_PORT)
    )
    permission_url = permission_endpoint

    datastore_reader_endpoint = (
        DEFAULT_PROTOCOL
        + "://"
        + get_env("DATASTORE_READER_HOST", DEFAULT_HOST)
        + ":"
        + get_env("DATASTORE_READER_PORT", DEFAULT_DATASTORE_READER_PORT)
    )
    datastore_reader_url = datastore_reader_endpoint + "/internal/datastore/reader"

    datastore_writer_endpoint = (
        DEFAULT_PROTOCOL
        + "://"
        + get_env("DATASTORE_WRITER_HOST", DEFAULT_HOST)
        + ":"
        + get_env("DATASTORE_WRITER_PORT", DEFAULT_DATASTORE_WRITER_PORT)
    )
    datastore_writer_url = datastore_writer_endpoint + "/internal/datastore/writer"

    return Environment(
        authentication_url=authentication_url,
        permission_url=permission_url,
        datastore_reader_url=datastore_reader_url,
        datastore_writer_url=datastore_writer_url,
    )


def get_env(env: str, default: str) -> str:
    value = os.environ.get(env)
    if value is None:
        print(f"Warn: get fallback for {env}: {default}")
        return default
    else:
        return value
