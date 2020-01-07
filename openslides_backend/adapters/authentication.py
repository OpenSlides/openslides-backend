from ..utils.types import Headers


class AuthenticationAdapter:
    """
    Adapter to connect to auth service.
    """

    def __init__(self, auth_url: str) -> None:
        self.url = auth_url

    def get_user(self, headers: Headers) -> int:
        raise
