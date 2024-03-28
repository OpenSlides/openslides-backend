from unittest import TestCase
from unittest.mock import MagicMock, patch

from openslides_backend.http.http_exceptions import MethodNotAllowed
from openslides_backend.shared.exceptions import ActionException, PermissionDenied
from openslides_backend.shared.interfaces.wsgi import View, WSGIApplication
from tests.system.util import create_base_test_application

from ..util import Client


def create_test_application(view: type[View]) -> WSGIApplication:
    return create_base_test_application(view, MagicMock())


class TestHttpExceptions(TestCase):
    def setUp(self) -> None:
        self.application = create_test_application(MagicMock)
        self.client = Client(self.application)
        self.view = MagicMock()
        self.patcher = patch.object(self.application, "view")
        view_type = self.patcher.start()
        view_type.return_value = self.view

    def tearDown(self) -> None:
        self.patcher.stop()

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
        self.view.dispatch.assert_called()
