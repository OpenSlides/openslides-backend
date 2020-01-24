from typing import Any, Dict, List

from mypy_extensions import TypedDict
from typing_extensions import Protocol

from ..shared.interfaces import LoggingModule, Services
from ..shared.patterns import FullQualifiedField

RestrictionBlob = TypedDict("RestrictionBlob", {"user_id": int, "fqfields": List[str]})
Payload = List[RestrictionBlob]
RestrictionResponse = List[Dict[FullQualifiedField, Any]]


class Restrictions(Protocol):  # pragma: no cover
    """
    Interface for restrictions (sub)service.

    The handle_request method raises RestrictionException if the request fails.
    """

    def handle_request(
        self, payload: Payload, logging: LoggingModule, services: Services,
    ) -> RestrictionResponse:
        ...
