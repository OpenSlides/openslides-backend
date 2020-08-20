from .base import BasePresenterTestCase


class TestInitialData(BasePresenterTestCase):
    def test_simple(self) -> None:
        status_code, data = self.request("initial-data")
        self.assertEqual(status_code, 200)
        expected = {
            "privacy_policy": "The PP",
            "legal_notice": "The LN",
            "theme": "openslides-default",
            "logo_web_header_path": None,
            "login_info_text": None,
            "saml_settings": None,
        }
        self.assertEqual(data, expected)
