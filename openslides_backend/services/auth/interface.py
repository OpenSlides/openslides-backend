from typing import Any, Optional, Protocol, Tuple

from authlib import AUTHENTICATION_HEADER, COOKIE_NAME  # noqa

from ..shared.authenticated_service import AuthenticatedServiceInterface


class AuthenticationService(AuthenticatedServiceInterface, Protocol):
    """
    Interface of the Auth Service.
    """

    auth_handler: Any

    def authenticate(self) -> Tuple[int, Optional[str]]:
        """
        A request to get knowledge about themselves. This information is contained in the payload of
        a Token. So, this function handles the refreshing of a Token.

        Sends back a new Token.

        Throws an exception, if the cookie is empty or the transmitted sessionId is wrong.

        Authentication data must be set beforehand via set_authentication.
        """

    def authenticate_only_refresh_id(self) -> int:
        """
        Analogous to authenticate, but works without the token.
        Therefore returns only the user id.

        Authentication data must be set beforehand via set_authentication.
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

    def create_authorization_token(self, user_id: int, email: str) -> str:
        """
        Creates a jsonwebtoken with user_id and email and returns it.
        """

    def verify_authorization_token(self, user_id: int, token: str) -> bool:
        """
        Checks the user_id with the token, returns true if okay else false.
        """

    def clear_all_sessions(self) -> None:
        """
        Clears all sessions of the user.

        Authentication data must be set beforehand via set_authentication.
        """
