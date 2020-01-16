from typing import Any, Dict, List

from typing_extensions import Protocol

from ..adapters.protocols import Headers


class Request(Protocol):
    """
    Interface for incoming requests.
    """

    headers: Headers
    is_json: bool
    json: List[Dict[Any, Any]]


class CustomException(Protocol):
    """
    Interface for custom exceptions.
    """

    message: str
