from typing import Any, Dict, List

from typing_extensions import Protocol

from ..adapters.providers import HeadersProvider


class RequestProvider(Protocol):
    """
    Interface for incoming requests.
    """

    headers: HeadersProvider
    is_json: bool
    json: List[Dict[Any, Any]]
