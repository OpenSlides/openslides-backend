import json
from unittest import TestCase
from unittest.mock import MagicMock

from openslides_backend.presenter import PresenterBlob
from openslides_backend.presenter.presenter import PresenterHandler
from openslides_backend.shared.exceptions import PresenterException

from ..utils import Client, ResponseWrapper, create_test_application


class PresenterBaseUnitTester(TestCase):
    def setUp(self) -> None:
        self.presenter_handler = PresenterHandler()
        self.user_id = 0

    def test_with_bad_key(self) -> None:
        payload = [
            PresenterBlob(
                user_id=self.user_id, presentation="non_existing_presentation",
            )
        ]
        with self.assertRaises(PresenterException) as context_manager:
            self.presenter_handler.handle_request(
                payload=payload, logging=MagicMock(), services=MagicMock(),
            )
        self.assertEqual(
            context_manager.exception.message,
            f"Presentation non_existing_presentation does not exist.",
        )

    def test_presenter_handler(self) -> None:
        payload = [PresenterBlob(user_id=self.user_id, presentation="dummy",)]
        response = self.presenter_handler.handle_request(
            payload=payload, logging=MagicMock(), services=MagicMock(),
        )
        expected = [{"dummy": "dummy"}]
        self.assertEqual(response, expected)


class PresenterBaseWSGITester(TestCase):
    def setUp(self) -> None:
        self.user_id = 0
        self.application = create_test_application(
            user_id=self.user_id, view_name="PresenterView"
        )

    def test_wsgi_request_empty(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get("/", json=[{"user_id": self.user_id, "presentation": ""}])
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0].presentation must be longer than or equal to 1 characters",
            str(response.data),
        )

    def test_wsgi_request_fuzzy(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get(
            "/",
            json=[
                {"user_id": self.user_id, "presentation": "non_existing_presentation"}
            ],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Presentation non_existing_presentation does not exist.",
            str(response.data),
        )

    def test_wsgi_request_correct_1(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get(
            "/", json=[{"user_id": self.user_id, "presentation": "dummy"}],
        )
        self.assertEqual(response.status_code, 200)
        expected = [{"dummy": "dummy"}]
        self.assertEqual(json.loads(response.data), expected)
