from typing import Any, Protocol

from ..shared.authenticated_service import AuthenticatedServiceInterface


class AuthenticationService(AuthenticatedServiceInterface, Protocol):
    """
    Interface of the Auth Service.
    """

    auth_handler: Any

    def authenticate(self) -> tuple[int, str | None]:
        """
        A request to get knowledge about themselves. This information is contained in the payload of
        a Token. So, this function handles the refreshing of a Token.

        Sends back a new Token.

        Throws an exception, if the cookie is empty or the transmitted sessionId is wrong.

        Authentication data must be set beforehand via set_authentication.
        """

    def decode_logout_token(self, encoded_logout_token: str) -> str:
        """
        Decodes a request to logout and block an active session id. Takes an encoded JWT token containing a
        logout token as a parameter

        Throws an exception, if the request is invalid
        """

    def hash(self, toHash: str) -> str:
        """
        Hashes a given value. A random salt (64bit) is generated and added to the hashed value.
        Returns the hashed value. The hashed value is structured as follows: [salt + hash].
        """

    def is_equal(self, toHash: str, toCompare: str) -> bool:
        """
        Compares a given value with an given hash.
        toHash is the password in plaint text which should be compared with the hashed value
        given in toCompare.
        Returns a boolean, if the hashed value of the given value is equals to the passed hash.
        """

    def is_anonymous(self, user_id: int) -> bool:
        """
        Checks if the given user is anonymous or not.
        """

    def is_session_id_blocked(self, session_id: str) -> bool:
        """
        Checks if session_id is blocked and thereby invalid
        """

