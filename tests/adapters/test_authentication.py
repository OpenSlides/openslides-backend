import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from unittest import TestCase

import simplejson as json
from werkzeug.datastructures import Headers

from openslides_backend.adapters.authentication import AuthenticationAdapter


class FakeServerRequestHandler(BaseHTTPRequestHandler):
    """
    Request handler for fake server.
    """

    def __init__(self, user_id: int, *args: Any, **kwargs: Any) -> None:
        self.user_id = user_id
        super().__init__(*args, **kwargs)

    def do_POST(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(str.encode(json.dumps({"user_id": self.user_id})))


class FakeServerRequestHandlerFactory:
    """
    Factory to generate customized request handlers.
    """

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def __call__(self, *args: Any, **kwargs: Any) -> FakeServerRequestHandler:
        return FakeServerRequestHandler(self.user_id, *args, **kwargs)


class FakeServer:
    """
    Simple Python HTTP server for testing purposes.
    """

    # TODO: Make this server faster.

    def __init__(self, host: str, port: int, user_id: int) -> None:
        self.user_id = user_id
        self.server_address = (host, port)
        self.httpd = HTTPServer(
            self.server_address, FakeServerRequestHandlerFactory(self.user_id)
        )
        self.thread = threading.Thread(target=self.httpd.serve_forever)

    def __enter__(self) -> None:
        self.thread.start()

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        self.httpd.shutdown()


class AuthenticationAdapterTester(TestCase):
    def setUp(self) -> None:
        self.host = "localhost"
        self.port = 9000

    def test_get_anonymous(self) -> None:
        with FakeServer(self.host, self.port, 0):
            auth = AuthenticationAdapter(f"http://{self.host}:{self.port}")
            headers = Headers()
            user_id = auth.get_user(headers)
            self.assertEqual(user_id, 0)

    def test_some_user(self) -> None:
        expected_user_id = 5262746456
        with FakeServer(self.host, self.port, expected_user_id):
            auth = AuthenticationAdapter(f"http://{self.host}:{self.port}")
            headers = Headers()
            user_id = auth.get_user(headers)
            self.assertEqual(user_id, expected_user_id)
