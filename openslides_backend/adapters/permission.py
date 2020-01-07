class PermissionAdapter:
    """
    Adapter to connect to permission service.
    """

    def __init__(self, permission_url: str) -> None:
        self.url = permission_url
        # self.headers = {"Content-Type": "application/json"}

    def has_perm(self, user_id: int, permission: str) -> None:
        raise
