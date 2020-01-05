from typing import Any, Callable, Dict, Text

from mypy_extensions import TypedDict

Environment = TypedDict(
    "Environment",
    {
        "database_url": str,
        "event_store_url": str,
        "auth_url": str,
        "worker_timeout": int,
    },
)

ApplicationConfig = TypedDict("ApplicationConfig", {"environment": Environment})

StartResponse = Callable

WSGIEnvironment = Dict[Text, Any]

Headers = Any  # TODO

Event = TypedDict("Event", {"foo": str})

KEYSEPARATOR = "/"


class FullQualifiedId:
    """
    Part of a full qualified field (also known as "key"),
    e. g. motions.change_recommendation/42
    """

    def __init__(self, collection: str, id: int) -> None:
        self.collection = collection
        self.id = id

    def __str__(self) -> str:
        return f"{self.collection}{KEYSEPARATOR}{self.id}"


class Collection:
    """
    The first part of a full qualified field (also known as "key")
    """

    def __init__(self, collection: str) -> None:
        self.collection = collection

    def __str__(self) -> str:
        return self.collection
