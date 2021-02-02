import json
from typing import Any, Dict, List

import requests

from ...shared.exceptions import PermissionException
from ...shared.interfaces.logging import LoggingModule
from .interface import PermissionService


class PermissionHTTPAdapter(PermissionService):
    """
    Adapter to connect to permission service.
    """

    def __init__(self, permission_url: str, logging: LoggingModule) -> None:
        self.endpoint = permission_url + "/is_allowed"
        self.logger = logging.getLogger(__name__)

    def is_allowed(
        self, name: str, user_id: int, data_list: List[Dict[str, Any]]
    ) -> bool:
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
            self.logger.error(
                f"Cannot reach the permission service on {self.endpoint}. Error: {e}"
            )
            raise PermissionException(
                f"Cannot reach the permission service on {self.endpoint}."
            )

        content = response.json()
        self.logger.debug(
            f"Permission service response with status code {response.status_code}: {str(content)}"
        )

        if response.status_code >= 400:
            error_message = f"Permission service sends HTTP {response.status_code} with the following content: {str(content)}."
            self.logger.error(error_message)
            raise PermissionException(
                f"Permission service sends HTTP {response.status_code}."
            )

        if not isinstance(content, bool):
            self.logger.error(f"Bad response from permission service: {str(content)}.")
            raise PermissionException("Bad response from permission service.")

        return content
