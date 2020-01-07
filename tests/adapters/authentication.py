from typing import Any

from openslides_backend.utils.types import Headers


class AuthenticationTestAdapter:
    """
    Test adapter for authentication queries.

    See openslides_backend.services.providers.AuthenticationProvider for
    implementation.
    """

    def __init__(*args: Any, **kwargs: Any) -> None:
        pass

    def get_user(self, headers: Headers) -> int:
        return 27
