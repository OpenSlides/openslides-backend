import os
from typing import TypedDict

Environment = TypedDict(
    "Environment",
    {
        "media_url": str,
        "datastore_reader_url": str,
        "datastore_writer_url": str,
        "vote_url": str,
    },
)

DEFAULTS = {
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
    "VOTE_PROTOCOL": "http",
    "VOTE_HOST": "vote",
    "VOTE_PORT": "9013",
    "VOTE_PATH": "/internal/vote",
}


def get_environment() -> Environment:
    """
    Parses environment variables and sets their defaults if they do not exist.
    """
    return Environment(
        media_url=get_endpoint("MEDIA"),
        datastore_reader_url=get_endpoint("DATASTORE_READER"),
        datastore_writer_url=get_endpoint("DATASTORE_WRITER"),
        vote_url=get_endpoint("VOTE"),
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
