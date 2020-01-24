from typing import List


class PermissionHTTPAdapter:
    """
    Adapter to connect to permission service.
    """

    def __init__(self, permission_url: str) -> None:
        self.url = permission_url
        # self.headers = {"Content-Type": "application/json"}

    def has_perm(self, user_id: int, permission: str) -> bool:
        raise

    def get_all(self, user_id: int) -> List[str]:
        raise
