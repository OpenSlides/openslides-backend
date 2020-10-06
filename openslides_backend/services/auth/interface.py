from typing import Dict, Optional, Protocol, Tuple

from ...shared.interfaces import Headers

GUEST_USER_ID = 0

AUTHENTICATION_HEADER = "Authentication"


class AuthenticationService(Protocol):
    """
    Interface of the Auth Service.
    """

    def authenticate(
        self, headers: Headers, cookies: Dict[str, str]
    ) -> Tuple[int, Optional[str]]:
        """
        A request to get knowledge about themselves. This information is contained in the payload of
        a Token. So, this function handles the refreshing of a Token.

        Sends back a new Token.

        Throws an exception, if the cookie is empty or the transmitted sessionId is wrong.
        """

    def hash(self, toHash: str) -> str:
        """
        Hashes a given value. A random salt (64bit) is generated and added to the hashed value.
        Returns the hashed value. The hashed value is structured as follows: [salt + hash].
        """

    def is_equals(self, hash: str, toCompare: str) -> bool:
        """
        Compares a given value with an given hash.
        Returns a boolean, if the hashed value of the given value is equals to the passed hash.
        """
