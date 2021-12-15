from typing import Any, Dict, cast
from unittest.mock import MagicMock

import requests
from authlib import AUTHENTICATION_HEADER, COOKIE_NAME
from werkzeug.test import Client as WerkzeugClient
from werkzeug.test import TestResponse
from werkzeug.wrappers import Response as BaseResponse

from openslides_backend.shared.exceptions import AuthenticationException
from openslides_backend.shared.interfaces.wsgi import Headers, WSGIApplication
from openslides_backend.shared.patterns import (
    KEYSEPARATOR,
    Collection,
    FullQualifiedField,
    FullQualifiedId,
)


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


class Client(WerkzeugClient):
    application: WSGIApplication

    def __init__(
        self, application: WSGIApplication, username: str = None, password: str = None
    ):
        super().__init__(application, ResponseWrapper)
        self.application = application
        self.headers = Headers()
        self.cookies: Dict[str, str] = {}
        if username and password is not None:
            self.login(username, password)

    def login(self, username: str, password: str) -> None:
        auth_endpoint = self.application.services.authentication().auth_handler.http_handler.get_endpoint(
            MagicMock()
        )
        url = f"{auth_endpoint}/system/auth/login"
        try:
            response = requests.post(
                url, json={"username": username, "password": password}
            )
        except requests.exceptions.ConnectionError as e:
            raise AuthenticationException(
                f"Cannot reach the authentication service on {url}. Error: {e}"
            )
        assert response.status_code == 200
        # save access token and refresh id for subsequent requests
        self.set_cookie("localhost", COOKIE_NAME, response.cookies.get(COOKIE_NAME))
        self.cookies = {COOKIE_NAME: response.cookies.get(COOKIE_NAME)}
        self.headers[AUTHENTICATION_HEADER] = response.headers[AUTHENTICATION_HEADER]

    def get(self, *args: Any, **kwargs: Any) -> Response:
        """
        Overwrite the return type since it's actually our Response type.
        """
        return cast(Response, super().get(*args, **kwargs))

    def post(self, *args: Any, **kwargs: Any) -> Response:
        """
        Overwrite the return type since it's actually our Response type. Also add headers.
        """
        kw_headers = kwargs.pop("headers", {})
        headers = {**self.headers, **kw_headers}
        return cast(Response, super().post(*args, headers=headers, **kwargs))


def get_fqid(value: str) -> FullQualifiedId:
    """
    Returns a FullQualifiedId parsed from the given value.
    """
    collection, id = value.split(KEYSEPARATOR)
    return FullQualifiedId(Collection(collection), int(id))


def get_fqfield(value: str) -> FullQualifiedField:
    """
    Returns a FullQualifiedField parsed from the given value.
    """
    collection, id, field = value.split(KEYSEPARATOR)
    return FullQualifiedField(Collection(collection), int(id), field)


def get_id_from_fqid(fqid: str) -> int:
    id = fqid.split(KEYSEPARATOR)[1]
    return int(id)


def get_collection_from_fqid(fqid: str) -> Collection:
    return Collection(fqid.split(KEYSEPARATOR)[0])
