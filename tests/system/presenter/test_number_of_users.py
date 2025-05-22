from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from .base import BasePresenterTestCase


class TestNumberOfUsers(BasePresenterTestCase):
    def test_number_of_users_no_limit(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"limit_of_users": 0},
                "user/2": {"username": "kimi", "is_active": True},
                "user/3": {"username": "kimi", "is_active": True},
            }
        )
        status_code, data = self.request(
            "number_of_users", {"number_of_users_to_add_or_activate": 100}
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"possible": True})

    def test_number_of_users_limit_plus_1(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"limit_of_users": 3},
                "user/2": {"username": "kimi", "is_active": True},
                "user/3": {"username": "kimi", "is_active": True},
            }
        )
        status_code, data = self.request(
            "number_of_users", {"number_of_users_to_add_or_activate": 1}
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"possible": False})

    def test_number_of_users_limit_okay(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"limit_of_users": 4},
                "user/2": {"username": "kimi", "is_active": True},
                "user/3": {"username": "kimi", "is_active": False},
            }
        )
        status_code, data = self.request(
            "number_of_users", {"number_of_users_to_add_or_activate": 2}
        )
        print(data)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"possible": True})

    def test_number_of_users_empty_payload(self) -> None:
        self.set_models({ONE_ORGANIZATION_FQID: {"limit_of_users": 4}})
        status_code, data = self.request("number_of_users", {})
        self.assertEqual(status_code, 400)
