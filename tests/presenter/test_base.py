import json
from unittest import TestCase
from unittest.mock import MagicMock

from openslides_backend.presenter import PresenterBlob
from openslides_backend.presenter.presenter import PresenterHandler
from openslides_backend.shared.exceptions import PresenterException

from ..utils import Client, ResponseWrapper, create_test_application


class PresenterBaseUnitTester(TestCase):
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

    def test_initial_data(self) -> None:
        payload = [PresenterBlob(presenter="initial-data", data={})]
        response = self.presenter_handler.handle_request(
            payload=payload, user_id=self.user_id,
        )
        expected = [
            {
                "privacy_policy": "The PP",
                "legal_notice": "The LN",
                "theme": "openslides-default",
                "logo_web_header_path": None,
                "login_info_text": None,
                "saml_settings": None,
            }
        ]
        self.assertEqual(response, expected)

    def test_whoami(self) -> None:
        payload = [PresenterBlob(presenter="whoami", data={})]
        response = self.presenter_handler.handle_request(
            payload=payload, user_id=self.user_id,
        )
        expected = [
            {
                "auth_type": "default",
                "permissions": [],
                "user_id": 1,
                "guest_enabled": True,
                "groups_id": [2],
                "short_name": "username",
            }
        ]
        self.assertEqual(response, expected)


class PresenterBaseWSGITester(TestCase):
    def setUp(self) -> None:
        self.user_id = 0
        self.application = create_test_application(
            user_id=self.user_id, view_name="PresenterView"
        )

    def test_wsgi_request_empty(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get("/", json=[{"presenter": ""}])
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0].presenter must be longer than or equal to 1 characters",
            str(response.data),
        )

    def test_wsgi_request_fuzzy(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get("/", json=[{"presenter": "non_existing_presenter"}],)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Presenter non_existing_presenter does not exist.", str(response.data),
        )

    def test_wsgi_request_correct_1(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get("/", json=[{"presenter": "initial-data"}],)
        self.assertEqual(response.status_code, 200)
        expected = [
            {
                "privacy_policy": "The PP",
                "legal_notice": "The LN",
                "theme": "openslides-default",
                "logo_web_header_path": None,
                "login_info_text": None,
                "saml_settings": None,
            }
        ]
        self.assertEqual(json.loads(response.data), expected)

    def test_wsgi_whoami(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get("/", json=[{"presenter": "whoami"}],)
        self.assertEqual(response.status_code, 200)
        expected = [
            {
                "auth_type": "default",
                "permissions": [],
                "user_id": 1,
                "guest_enabled": True,
                "groups_id": [2],
                "short_name": "username",
            }
        ]
        self.assertEqual(json.loads(response.data), expected)
