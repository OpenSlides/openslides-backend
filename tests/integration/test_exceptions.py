import os
from unittest import TestCase
from unittest.mock import MagicMock

from openslides_backend.http.http_exceptions import MethodNotAllowed
from openslides_backend.shared.env import Environment
from openslides_backend.shared.exceptions import ActionException, PermissionDenied
from openslides_backend.shared.interfaces.wsgi import View, WSGIApplication
from openslides_backend.wsgi import OpenSlidesBackendWSGI

from ..util import Client


def create_test_application(view: type[View]) -> WSGIApplication:
    application_factory = OpenSlidesBackendWSGI(
        env=Environment(os.environ),
        logging=MagicMock(),
        view=view,
        services=MagicMock(),
    )
    application = application_factory.setup()
    return application


class TestHttpExceptions(TestCase):
    def setUp(self) -> None:
        self.view = MagicMock()
        self.view_type = MagicMock(return_value=self.view)
        self.application = create_test_application(self.view_type)
        self.client = Client(self.application)

    def test_bad_request(self) -> None:
        self.view.dispatch.side_effect = ActionException("test")
        response = self.client.post("/", json=[{"action": "agenda_item.create"}])
        self.assertEqual(response.status_code, 400)
        self.view.dispatch.assert_called()
        data = response.json
        self.assertEqual(data.get("message"), "test")

    def test_forbidden(self) -> None:
        self.view.dispatch.side_effect = PermissionDenied("test")
        response = self.client.post("/", json=[{"action": "agenda_item.create"}])
        self.assertEqual(response.status_code, 403)
        self.view.dispatch.assert_called()
        data = response.json
        self.assertEqual(data.get("message"), "test")

    def test_method_not_allowed(self) -> None:
        self.view.dispatch.side_effect = MethodNotAllowed()
        response = self.client.get("/", json=[{"action": "agenda_item.create"}])
        self.assertEqual(response.status_code, 405)
