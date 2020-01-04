from ..utils.wrappers import Request


class AuthAdapter:
    """
    Adapter to connect to auth service.
    """

    def __init__(self, auth_url: str) -> None:
        self.url = auth_url

    def get_user(self, request: Request) -> int:
        return 0
