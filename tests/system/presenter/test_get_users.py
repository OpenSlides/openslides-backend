from openslides_backend.permissions.management_levels import OrganizationManagementLevel

from .base import BasePresenterTestCase


class TestGetUsers(BasePresenterTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user2 = {
            "username": "florian",
            "first_name": "Florian",
            "last_name": "Freiheit",
        }
        self.user3 = {
            "username": "test",
            "first_name": "Testy",
            "last_name": "Tester",
        }
        self.user4 = {
            "username": "john",
            "first_name": "John",
            "last_name": "Xylon",
        }
        self.user5 = {
            "username": "xorr",
            "first_name": "John",
            "last_name": "Xorr",
        }

    def test_pagination(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/2": self.user2,
                "user/3": {**self.user3, "username": "goofi"},
                "user/4": self.user4,
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
        self.create_meeting()
        self.set_models(
            {
                "user/2": self.user2,
                "user/3": self.user3,
                "user/4": self.user4,
                "user/5": self.user5,
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

    def test_keywords_paginated(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/2": self.user2,
                "user/3": self.user3,
                "user/4": self.user4,
                "user/5": self.user5,
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
        self.create_meeting()
        self.set_models(
            {
                "user/2": self.user2,
                "user/3": self.user3,
                "user/4": self.user4,
                "user/5": {**self.user5, "last_name": "Xzrr"},
            }
        )
        status_code, data = self.request("get_users", {})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"users": [1, 2, 3, 4, 5]})

    def test_check_sort_title(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/2": {**self.user2, "title": "Accc"},
                "user/3": {**self.user3, "title": "Cbbb"},
                "user/4": {**self.user4, "title": "Edfff"},
                "user/5": self.user5,
            }
        )
        status_code, data = self.request(
            "get_users", {"sort_criteria": ["title", "username"]}
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"users": [1, 5, 2, 3, 4]})

    def test_get_users_no_permissions(self) -> None:
        self.set_models({"user/1": {"organization_management_level": None}})
        status_code, data = self.request("get_users", {"sort_criteria": ["username"]})
        self.assertEqual(status_code, 403)

    def test_get_users_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                }
            }
        )
        status_code, data = self.request("get_users", {"sort_criteria": ["username"]})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"users": [1]})

    def test_request_without_token(self) -> None:
        self.client.auth_data.pop("access_token", None)
        status_code, data = self.request("get_users", {})
        self.assertEqual(status_code, 403)
