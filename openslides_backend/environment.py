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

DEFAULTS = {
    "AUTHENTICATION_URL": "http://localhost:9004",
    "PERMISSION_URL": "http://localhost:9005",
    "DATASTORE_READER_URL": "http://localhost:9010/internal/reader",
    "DATASTORE_WRITER_URL": "http://localhost:9011/internal/writer",
}


def get_environment() -> Environment:
    """
    Parses environment variables and sets their defaults if they do not exist.
    """
    return Environment(
        authentication_url=get_env("AUTHENTICATION_URL"),
        permission_url=get_env("PERMISSION_URL"),
        datastore_reader_url=get_env("DATASTORE_READER_URL"),
        datastore_writer_url=get_env("DATASTORE_WRITER_URL"),
    )


def get_env(var: str) -> str:
    value = os.environ.get(var)
    if value is None:
        default = DEFAULTS.get(var)
        if default is None:
            raise ValueError(f"Environment variable {var} does not exist.")
        return default
    return value
