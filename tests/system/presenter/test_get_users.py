from .base import BasePresenterTestCase
from openslides_backend.permissions.management_levels import OrganizationManagementLevel


class TestGetUsers(BasePresenterTestCase):
    def test_pagenation(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "meeting1"},
                "user/2": {
                    "username": "florian",
                    "first_name": "Florian",
                    "last_name": "Freiheit",
                },
                "user/3": {
                    "username": "goofi",
                    "first_name": "Testy",
                    "last_name": "Tester",
                },
                "user/4": {
                    "username": "john",
                    "first_name": "John",
                    "last_name": "Xylon",
                },
            }
        )
        status_code, data = self.request(
            "get_users",
            {
                "start_index": 1,
                "entries": 2,
                "sort_criteria": ["username"],
                "reverse": False,
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"users": [2, 3]})

    def test_keywords_filter(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "meeting1"},
                "user/2": {
                    "username": "florian",
                    "first_name": "Florian",
                    "last_name": "Freiheit",
                },
                "user/3": {
                    "username": "test",
                    "first_name": "Testy",
                    "last_name": "Tester",
                },
                "user/4": {
                    "username": "john",
                    "first_name": "John",
                    "last_name": "Xylon",
                },
                "user/5": {
                    "username": "xorr",
                    "first_name": "John",
                    "last_name": "Xorr",
                },
            }
        )
        status_code, data = self.request(
            "get_users",
            {
                "start_index": 0,
                "entries": 100,
                "sort_criteria": ["first_name", "username"],
                "reverse": True,
                "filter": "John",
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"users": [5, 4]})

    def test_keywords_pagenated(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "meeting1"},
                "user/2": {
                    "username": "florian",
                    "first_name": "Florian",
                    "last_name": "Freiheit",
                },
                "user/3": {
                    "username": "test",
                    "first_name": "Testy",
                    "last_name": "Tester",
                },
                "user/4": {
                    "username": "john",
                    "first_name": "John",
                    "last_name": "Xylon",
                },
                "user/5": {
                    "username": "xorr",
                    "first_name": "John",
                    "last_name": "Xorr",
                },
            }
        )
        status_code, data = self.request(
            "get_users",
            {
                "start_index": 1,
                "entries": 1,
                "sort_criteria": ["first_name", "username"],
                "reverse": True,
                "filter": "John",
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"users": [4]})

    def test_check_defaults(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "meeting1"},
                "user/2": {
                    "username": "florian",
                    "first_name": "Florian",
                    "last_name": "Freiheit",
                },
                "user/3": {
                    "username": "test",
                    "first_name": "Testy",
                    "last_name": "Tester",
                },
                "user/4": {
                    "username": "john",
                    "first_name": "John",
                    "last_name": "Xylon",
                },
                "user/5": {
                    "username": "xorr",
                    "first_name": "John",
                    "last_name": "Xzrr",
                },
            }
        )
        status_code, data = self.request("get_users", {})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"users": [1, 2, 3, 4, 5]})

    def test_check_sort_title(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "meeting1"},
                "user/2": {
                    "username": "florian",
                    "first_name": "Florian",
                    "last_name": "Freiheit",
                    "title": "Accc",
                },
                "user/3": {
                    "username": "test",
                    "first_name": "Testy",
                    "last_name": "Tester",
                    "title": "Cbbb",
                },
                "user/4": {
                    "username": "john",
                    "first_name": "John",
                    "last_name": "Xylon",
                    "title": "Edfff",
                },
                "user/5": {
                    "username": "xorr",
                    "first_name": "John",
                    "last_name": "Xorr",
                },
            }
        )
        status_code, data = self.request(
            "get_users", {"sort_criteria": ["title", "username"]}
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"users": [1, 5, 2, 3, 4]})


    def test_get_users_no_permissions(self) -> None:
        self.set_models({"user/1": {"organization_management_level": None}})
        status_code, data = self.request(
            "get_users", {"sort_criteria": ["username"]}
        )
        self.assertEqual(status_code, 403)

    def test_get_users_permissions(self) -> None:
        self.set_models({"user/1": {"organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS}})
        status_code, data = self.request(
            "get_users", {"sort_criteria": ["username"]}
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"users": [1]})

