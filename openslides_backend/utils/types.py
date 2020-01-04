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

Event = TypedDict("Event", {"foo": str})
