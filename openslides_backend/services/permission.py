from typing import Any


class PermissionHTTPAdapter:
    """
    Adapter to connect to permission service.
    """

    def __init__(self, permission_url: str) -> None:
        self.url = permission_url
        # self.headers = {"Content-Type": "application/json"}

    def check_action(self, user_id: int, action: str, data: Any) -> bool:
        # TODO: Do not use hardcoded value here but send request to
        # permission service.
        return True
