import os

from mypy_extensions import TypedDict

Environment = TypedDict(
    "Environment",
    {
        "authentication_url": str,
        "permission_url": str,
        "media_url": str,
        "datastore_reader_url": str,
        "datastore_writer_url": str,
    },
)

DEFAULTS = {
    "AUTH_PROTOCOL": "http",
    "AUTH_HOST": "localhost",
    "AUTH_PORT": "9004",
    "AUTH_PATH": "/internal/auth",
    "PERMISSION_PROTOCOL": "http",
    "PERMISSION_HOST": "localhost",
    "PERMISSION_PORT": "9005",
    "PERMISSION_PATH": "",
    "MEDIA_PROTOCOL": "http",
    "MEDIA_HOST": "localhost",
    "MEDIA_PORT": "9006",
    "MEDIA_PATH": "/internal/media",
    "DATASTORE_READER_PROTOCOL": "http",
    "DATASTORE_READER_HOST": "localhost",
    "DATASTORE_READER_PORT": "9010",
    "DATASTORE_READER_PATH": "/internal/datastore/reader",
    "DATASTORE_WRITER_PROTOCOL": "http",
    "DATASTORE_WRITER_HOST": "localhost",
    "DATASTORE_WRITER_PORT": "9011",
    "DATASTORE_WRITER_PATH": "/internal/datastore/writer",
}


def get_environment() -> Environment:
    """
    Parses environment variables and sets their defaults if they do not exist.
    """
    return Environment(
        authentication_url=get_endpoint("AUTH"),
        permission_url=get_endpoint("PERMISSION"),
        media_url=get_endpoint("MEDIA"),
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
