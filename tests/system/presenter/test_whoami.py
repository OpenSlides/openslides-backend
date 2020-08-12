from .base import BasePresenterTestCase


class TestWhoami(BasePresenterTestCase):
    def test_simple(self) -> None:
        status_code, data = self.request("whoami")
        self.assertEqual(status_code, 200)
        expected = {
            "auth_type": "default",
            "permissions": [],
            "user_id": 1,
            "guest_enabled": True,
            "groups_id": [2],
            "short_name": "username",
        }
        self.assertEqual(data, expected)
