from typing import Any, List, Optional, Tuple

from openslides_backend.shared.interfaces import Headers


class TestHeaders:
    """
    Headers object for testing.
    """

    def to_wsgi_list(self) -> List:
        return []


class AuthenticationTestAdapter:
    """
    Test adapter for authentication queries.
    See openslides_backend.adapters.protocols.AuthenticationProvider for
    implementation.
    It returns always the user id given at initialization.
    """

    def __init__(self, user_id: int = 0) -> None:
        self.user_id = user_id

    def get_user(self, headers: Headers) -> Tuple[int, Optional[str]]:
        return self.user_id, None

    def __call__(self, *args: Any, **kwargs: Any) -> "AuthenticationTestAdapter":
        return self
