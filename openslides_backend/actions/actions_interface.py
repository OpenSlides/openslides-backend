from typing import Any, Dict, List

from typing_extensions import Protocol

Payload = List[Dict[str, Any]]


class Actions(Protocol):
    """
    Interface for actions (sub)service.

    The handle_request method raises ActionException or PermissionDenied if
    the request fails.
    """

    def handle_request(
        self, payload: Payload, user_id: int, services: Any
    ) -> None:  # TODO: Remove services
        ...
