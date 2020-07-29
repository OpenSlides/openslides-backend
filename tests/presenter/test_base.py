from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock

from openslides_backend.presenter import PresenterBlob
from openslides_backend.presenter.presenter import PresenterHandler
from openslides_backend.shared.exceptions import PresenterException

from ..utils import Client, ResponseWrapper, create_test_application


class BasePresenterUnitTester(TestCase):
    def setUp(self) -> None:
        self.presenter_handler = PresenterHandler(
            logging=MagicMock(), services=MagicMock(),
        )
        self.user_id = 0

    def test_with_bad_key(self) -> None:
        payload = [PresenterBlob(presenter="non_existing_presenter", data={})]
        with self.assertRaises(PresenterException) as context_manager:
            self.presenter_handler.handle_request(
                payload=payload, user_id=self.user_id,
            )
        self.assertEqual(
            context_manager.exception.message,
            f"Presenter non_existing_presenter does not exist.",
        )


class BasePresenterWSGITester(TestCase):
    def setUp(self) -> None:
        self.user_id = 0
        self.client = self.get_client()

    def get_client(self, datastore_content: Any = {}, expected_write_data: str = "") -> Client:
        return Client(
            create_test_application(
                user_id=self.user_id,
                view_name="PresenterView",
                superuser=self.user_id,
                datastore_content=datastore_content,
                expected_write_data=expected_write_data,
            ),
            ResponseWrapper,
        )

    def test_wsgi_request_empty(self) -> None:
        response = self.client.get("/", json=[{"presenter": ""}])
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0].presenter must be longer than or equal to 1 characters",
            str(response.data),
        )

    def test_wsgi_request_fuzzy(self) -> None:
        response = self.client.get("/", json=[{"presenter": "non_existing_presenter"}],)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Presenter non_existing_presenter does not exist.", str(response.data),
        )
