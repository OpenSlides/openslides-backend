from typing import Any

from openslides_backend.utils.types import Headers


class AuthenticationTestAdapter:
    """
    Test adapter for authentication queries.

    See openslides_backend.services.providers.AuthenticationProvider for
    implementation.

    It returns always the user id given at initialization.
    """

    def __init__(self, user_id: int = 0) -> None:
        self.user_id = user_id

    def get_user(self, headers: Headers) -> int:
        return self.user_id

    def __call__(self, *args: Any, **kwargs: Any) -> "AuthenticationTestAdapter":
        return self
