import json

from openslides_backend.presenter import PresenterBlob

from .test_base import BasePresenterUnitTester, BasePresenterWSGITester


class InitialDataUnitTester(BasePresenterUnitTester):
    def test_unit_initial_data(self) -> None:
        payload = [PresenterBlob(presenter="initial-data")]
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


class InitialDataWSGITester(BasePresenterWSGITester):
    def test_wsgi_initial_data(self) -> None:
        response = self.client.post("/", json=[{"presenter": "initial-data"}],)
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
