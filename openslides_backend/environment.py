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
    "AUTHENTICATION_PROTOCOL": "http",
    "AUTHENTICATION_HOST": "localhost",
    "AUTHENTICATION_PORT": "9004",
    "AUTHENTICATION_PATH": "",
    "PERMISSION_PROTOCOL": "http",
    "PERMISSION_HOST": "localhost",
    "PERMISSION_PORT": "9005",
    "PERMISSION_PATH": "",
    "DATASTORE_READER_PROTOCOL": "http",
    "DATASTORE_READER_HOST": "localhost",
    "DATASTORE_READER_PORT": "9010",
    "DATASTORE_READER_PATH": "/internal/reader",
    "DATASTORE_WRITER_PROTOCOL": "http",
    "DATASTORE_WRITER_HOST": "localhost",
    "DATASTORE_WRITER_PORT": "9011",
    "DATASTORE_WRITER_PATH": "/internal/writer",
}


def get_environment() -> Environment:
    """
    Parses environment variables and sets their defaults if they do not exist.
    """
    return Environment(
        authentication_url=get_endpoint("AUTHENTICATION"),
        permission_url=get_endpoint("PERMISSION"),
        datastore_reader_url=get_endpoint("DATASTORE_READER"),
        datastore_writer_url=get_endpoint("DATASTORE_WRITER"),
    )


def get_endpoint(service: str) -> str:
    parts = {}
    for suffix in ("PROTOCOL", "HOST", "PORT", "PATH"):
        variable = "_".join((service, suffix))
        value = os.environ.get(variable)
        if value is None:
            default = DEFAULTS.get(variable)
            if default is None:
                raise ValueError(f"Environment variable {variable} does not exist.")
            parts[suffix] = default
        else:
            parts[suffix] = value
    return f"{parts['PROTOCOL']}://{parts['HOST']}:{parts['PORT']}{parts['PATH']}"
