from ..utils.types import Headers


class AuthenticationAdapter:
    """
    Adapter to connect to authentication service.
    """

    def __init__(self, authentication_url: str) -> None:
        self.url = authentication_url
        # self.headers = {"Content-Type": "application/json"}

    def get_user(self, headers: Headers) -> int:
        raise
