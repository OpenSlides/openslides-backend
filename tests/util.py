from collections.abc import Callable
from typing import Any, TypedDict, cast

import simplejson as json
from authlib import AUTHENTICATION_HEADER, COOKIE_NAME, AuthenticateException
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


class AuthData(TypedDict, total=False):
    """
    TypedDict for the authentication data. access_token must be inserted into the headers and the
    refresh_id as a cookie.
    """

    access_token: str
    refresh_id: str


class Client(WerkzeugClient):
    application: WSGIApplication

    def __init__(
        self,
        application: WSGIApplication,
        on_auth_data_changed: Callable[[AuthData], None] | None = None,
    ):
        super().__init__(application, ResponseWrapper)
        self.application = application
        self.auth_data: AuthData = {}
        self.on_auth_data_changed = on_auth_data_changed

    def login(self, username: str, password: str) -> None:
        handler = self.application.services.authentication().auth_handler.http_handler
        try:
            response = handler.send_request(
                "login",
                payload=json.dumps({"username": username, "password": password}),
                headers={"Content-Type": "application/json"},
            )
        except AuthenticateException as e:
            raise AuthenticationException(str(e))
        except Exception as e:
            raise AuthenticationException(str(e))
        assert response.status_code == 200
        # save access token and refresh id for subsequent requests
        self.update_auth_data(
            {
                "access_token": response.headers.get(AUTHENTICATION_HEADER),
                "refresh_id": response.cookies.get(COOKIE_NAME),
            }
        )

    def update_auth_data(self, auth_data: AuthData) -> None:
        """
        (Partially) updates the auth_data.
        """
        self.auth_data.update(auth_data)
        if "refresh_id" in self.auth_data:
            self.set_cookie(COOKIE_NAME, self.auth_data["refresh_id"])
        if self.on_auth_data_changed:
            self.on_auth_data_changed(self.auth_data)

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
            headers[AUTHENTICATION_HEADER] = self.auth_data["access_token"]
        response = cast(Response, super().post(*args, headers=headers, **kwargs))
        if AUTHENTICATION_HEADER in response.headers:
            self.update_auth_data(
                {"access_token": response.headers[AUTHENTICATION_HEADER]}
            )
        return response
