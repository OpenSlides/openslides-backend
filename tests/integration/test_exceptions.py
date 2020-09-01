import json
from unittest import TestCase
from unittest.mock import MagicMock

from openslides_backend.shared.exceptions import ViewException

from ..util import Client
from .util import create_test_application


class TestHttpExceptions(TestCase):
    def setUp(self) -> None:
        self.view = MagicMock()
        self.view_type = MagicMock(return_value=self.view)
        self.view_type.method = "POST"
        self.application = create_test_application(self.view_type)
        self.client = Client(self.application)

    def test_bad_request(self) -> None:
        self.view.dispatch.side_effect = ViewException("test", 400)
        response = self.client.post("/", json=[{"action": "agenda_item.create"}])
        self.assertEqual(response.status_code, 400)
        self.view.dispatch.assert_called()
        data = json.loads(response.data)
        self.assertEqual(data.get("message"), "test")

    def test_forbidden(self) -> None:
        self.view.dispatch.side_effect = ViewException("test", 403)
        response = self.client.post("/", json=[{"action": "agenda_item.create"}])
        self.assertEqual(response.status_code, 403)
        self.view.dispatch.assert_called()
        data = json.loads(response.data)
        self.assertEqual(data.get("message"), "test")

    def test_method_not_allowed(self) -> None:
        response = self.client.get("/", json=[{"action": "agenda_item.create"}])
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.data)
        assert data
