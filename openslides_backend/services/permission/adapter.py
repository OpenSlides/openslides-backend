import json
from typing import Any, Dict, List

import requests

from ...shared.exceptions import PermissionException
from ...shared.interfaces.logging import LoggingModule
from .interface import NotAllowed, PermissionService


class PermissionHTTPAdapter(PermissionService):
    """
    Adapter to connect to permission service.
    """

    def __init__(self, permission_url: str, logging: LoggingModule) -> None:
        self.endpoint = permission_url + "/is_allowed"
        self.logger = logging.getLogger(__name__)

    def is_allowed(
        self, name: str, user_id: int, data_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        payload = json.dumps(
            {"name": name, "user_id": user_id, "data": data_list}, separators=(",", ":")
        )

        try:
            response = requests.post(
                url=self.endpoint,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
        except requests.exceptions.ConnectionError as e:
            raise PermissionException(
                f"Cannot reach the permission service on {self.endpoint}. Error: {e}"
            )

        content = response.json()
        self.logger.debug(f"Permission service response: {str(content)}")

        if "error" in content:
            type = content["error"]["type"]
            msg = content["error"]["msg"]
            raise PermissionException(f"Error in permission service. {type}: {msg}")

        allowed = content.get("allowed", False)

        if not allowed:
            reason = content.get("reason")
            error_index = content.get("error_index")
            if error_index < 0:
                error_index = None

            # TODO: dev only. Log about missing perms check
            if "no such query" in reason:
                self.logger.warning(
                    f"Action {name} has no permission check. Return a default-true."
                )
                return [{} for _ in data_list]

            raise NotAllowed(reason, error_index)

        additions = content.get("additions") or []
        if not isinstance(additions, list):
            raise PermissionException("additions must be a list")

        for i in range(len(additions)):
            if additions[i] is None:
                additions[i] = {}
            if not isinstance(additions[i], dict):
                raise PermissionError(f"Addition {i} is not a dict")

        return additions
