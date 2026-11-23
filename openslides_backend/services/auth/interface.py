from typing import Any, Protocol

class AuthenticationService(Protocol):
    """
    Interface of the Auth Service.
    """
    def authenticate(self, auth_header: str) -> int:
        """
        Decodes a JWT token set by the IDP provider.
        Handles exceptions and validates audience/client source

        Returns the OpenSlides User ID contained within the JWT token on success
        Returns 0 as User ID, of authentication failed
        """

    def set_client_id(self, client_id: str) -> None:
        """
        Sets the expected client ID manually. If unset or empty, the client ID will be read from a volume mounted client ID file
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

