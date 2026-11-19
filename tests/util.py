from collections.abc import Callable
from typing import Any, TypedDict, cast

import jwt
import simplejson as json
from werkzeug.test import Client as WerkzeugClient
from werkzeug.test import TestResponse
from werkzeug.wrappers import Response as BaseResponse

from openslides_backend.shared.exceptions import AuthenticationException
from openslides_backend.shared.interfaces.wsgi import WSGIApplication


class ResponseWrapper(BaseResponse):
    """
    Customized response wrapper to adjust the typing of the json property.
    """

    @property
    def json(self) -> Any:
        return self.get_json()


class Response(ResponseWrapper, TestResponse):
    """
    Since the wrapper provided to the client can not inherit from TestResponse,
    we have to create this dummy class for correct typing of the Response.
    """

class IDPPayloadMock:
    def __init__(self, claims: dict):
        self.sub = claims.get("sub", "")  # User ID
        self.sid = claims.get("sid", "")  # Session ID
        self.os_id = claims.get("os_id", "")  # OS User ID

class AuthData(TypedDict, total=False):
    """
    TypedDict for the authentication data. Contains encoded mock JWT Access Token
    """

    access_token: IDPPayloadMock


class Client(WerkzeugClient):
    application: WSGIApplication
    mock_client_id = 400019926833692681

    def __init__(
        self,
        application: WSGIApplication,
        on_auth_data_changed: Callable[[AuthData], None] | None = None,
    ):
        super().__init__(application, ResponseWrapper)
        self.application = application
        self.auth_data: AuthData = {}
        self.on_auth_data_changed = on_auth_data_changed

    def logout(self) -> None:
        self.login(0)

    def login(self, user_id: int) -> None:
        self.set_client_id(mock_client_id)

        # Mock Claims
        claims = {
            "sub": sub,
            "sid": sid,
            "os_id": user_id,
            "aud": mock_client_id,
        }

        # JWT encode it
        token = jwt.encode(claims, "test-signing-key-for-jwt-encode-000000000000", algorithm="HS256")

        # Set as header
        header = "Bearer: " + payload

        # save access token and refresh id for subsequent requests
        self.update_auth_data({"access_token": header})

    def update_auth_data(self, auth_data: AuthData) -> None:
        """
        (Partially) updates the auth_data.
        """
        self.auth_data.update(auth_data)
        if self.on_auth_data_changed:
            self.on_auth_data_changed(self.auth_data)

    def get_auth_header(self) -> AuthData:
        return self.auth_data

    def get(self, *args: Any, **kwargs: Any) -> Response:
        """
        Overwrite the return type since it's actually our Response type.
        """
        return cast(Response, super().get(*args, **kwargs))

    def post(self, *args: Any, **kwargs: Any) -> Response:
        """
        Overwrite the return type since it's actually our Response type. Also add headers and update
        the access_token from the response.
        """
        headers = kwargs.pop("headers", {})
        if "access_token" in self.auth_data:
            headers["Authorization"] = self.auth_data["access_token"]
        response = cast(Response, super().post(*args, headers=headers, **kwargs))
        if "Authorization" in response.headers:
            self.update_auth_data({"access_token": response.headers["Authorization"]})
        return response
