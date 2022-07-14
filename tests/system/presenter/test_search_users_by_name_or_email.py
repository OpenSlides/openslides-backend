from openslides_backend.action.actions.user.user_scope_permission_check_mixin import (
    UserScope,
)
from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from openslides_backend.permissions.permissions import Permissions
from tests.system.util import Profiler, performance

from .base import BasePresenterTestCase


class TestSearchUsersByNameEmail(BasePresenterTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user2 = {
            "id": 2,
            "email": "user2@test.de",
            "first_name": "first2",
            "last_name": "last2",
            "username": "user2",
        }
        self.user3 = {
            "id": 3,
            "email": "userX@test.de",
            "first_name": "first3",
            "last_name": "last3",
            "username": "user3",
        }
        self.user4 = {
            "id": 4,
            "email": "userX@test.de",
            "first_name": "first4",
            "last_name": "last4",
            "username": "user4",
        }
        self.set_models(
            {
                "user/2": {
                    **self.user2,
                },
                "user/3": {
                    **self.user3,
                },
                "user/4": {
                    **self.user4,
                },
            }
        )

    def create_more_test_users(self, quantity: int = 1000) -> None:
        user_ids = list(range(5, quantity + 5))
        self.set_models(
            {
                **{
                    f"user/{i}": {
                        "id": i,
                        "email": f"userX{i}@test.de",
                        "first_name": f"first{i}",
                        "last_name": f"last{i}",
                        "username": f"user{i}",
                    }
                    for i in user_ids
                },
            }
        )

    def test_search_fields_variations(self) -> None:
        status_code, data = self.request(
            "search_users_by_name_or_email",
            {
                "permission_type": UserScope.Meeting.value,
                "permission_id": 1,
                "search": [
                    {
                        "username": "user2",
                    },
                    {
                        "email": "userX@test.de",
                    },
                    {
                        "username": "user2",
                        "email": "userX@test.de",
                    },
                ],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertCountEqual(
            data["user2/"],
            [self.user2],
        )
        self.assertCountEqual(
            data["/userX@test.de"],
            [self.user3, self.user4],
        )
        self.assertCountEqual(
            data["user2/userX@test.de"],
            [self.user2, self.user3, self.user4],
        )

    def test_search_ignore_case_strip(self) -> None:
        status_code, data = self.request(
            "search_users_by_name_or_email",
            {
                "permission_type": UserScope.Meeting.value,
                "permission_id": 1,
                "search": [
                    {
                        "email": " User2@test.de ",
                    },
                    {
                        "username": " USER2",
                    },
                ],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertCountEqual(
            data["/User2@test.de"],
            [self.user2],
        )
        self.assertCountEqual(
            data["USER2/"],
            [self.user2],
        )

    def test_search_wrong_permission_type(self) -> None:
        status_code, data = self.request(
            "search_users_by_name_or_email",
            {
                "permission_type": 4,
                "permission_id": 1,
                "search": [
                    {"username": "user2"},
                ],
            },
        )
        self.assertEqual(status_code, 400)
        self.assertIn("data.permission_type must be one of [1, 2, 3]", data["message"])

    def test_search_wrong_permission_id(self) -> None:
        status_code, data = self.request(
            "search_users_by_name_or_email",
            {
                "permission_type": UserScope.Organization.value,
                "permission_id": 0,
                "search": [
                    {"username": "user2"},
                ],
            },
        )
        self.assertEqual(status_code, 400)
        self.assertIn(
            "data.permission_id must be bigger than or equal to 1", data["message"]
        )

    def test_permission_organization_ok(self) -> None:
        self.update_model(
            "user/1",
            {
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
            },
        )
        status_code, _ = self.request(
            "search_users_by_name_or_email",
            {
                "permission_type": UserScope.Organization.value,
                "permission_id": 1,
                "search": [
                    {"username": "user2"},
                ],
            },
        )
        self.assertEqual(status_code, 200)

    def test_permission_organization_error(self) -> None:
        self.update_model("user/1", {"organization_management_level": None})
        status_code, data = self.request(
            "search_users_by_name_or_email",
            {
                "permission_type": UserScope.Organization.value,
                "permission_id": 1,
                "search": [
                    {"username": "user2"},
                ],
            },
        )
        self.assertEqual(status_code, 403)
        self.assertIn(
            "Missing OrganizationManagementLevel: can_manage_users", data["message"]
        )

    def test_permission_committee_ok(self) -> None:
        self.update_model(
            "user/1",
            {
                "organization_management_level": None,
                "committee_$_management_level": [CommitteeManagementLevel.CAN_MANAGE],
                "committee_$can_manage_management_level": [1],
            },
        )
        status_code, _ = self.request(
            "search_users_by_name_or_email",
            {
                "permission_type": UserScope.Committee.value,
                "permission_id": 1,
                "search": [
                    {"username": "user2"},
                ],
            },
        )
        self.assertEqual(status_code, 200)

    def test_permission_committee_error(self) -> None:
        self.update_model("user/1", {"organization_management_level": None})
        status_code, data = self.request(
            "search_users_by_name_or_email",
            {
                "permission_type": UserScope.Committee.value,
                "permission_id": 1,
                "search": [
                    {"username": "user2"},
                ],
            },
        )
        self.assertEqual(status_code, 403)
        self.assertIn(
            "Missing permission: CommitteeManagementLevel can_manage in committee 1",
            data["message"],
        )

    def test_permission_meeting_ok(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/1": {
                    "user_ids": [1],
                    "meeting_id": 1,
                    "permissions": [Permissions.User.CAN_MANAGE],
                },
            }
        )
        self.update_model(
            "user/1",
            {
                "group_$_ids": ["1"],
                "group_$1_ids": [1],
                "organization_management_level": None,
            },
        )
        status_code, _ = self.request(
            "search_users_by_name_or_email",
            {
                "permission_type": UserScope.Meeting.value,
                "permission_id": 1,
                "search": [
                    {"username": "user2"},
                ],
            },
        )
        self.assertEqual(status_code, 200)

    def test_permission_meeting_error(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
            }
        )
        self.update_model("user/1", {"organization_management_level": None})
        status_code, data = self.request(
            "search_users_by_name_or_email",
            {
                "permission_type": UserScope.Meeting.value,
                "permission_id": 1,
                "search": [
                    {"username": "user2"},
                ],
            },
        )
        self.assertEqual(status_code, 403)
        self.assertIn(
            "Missing permission: Permission user.can_manage in meeting 1",
            data["message"],
        )

    def test_permission_meeting_via_committee_ok(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
            }
        )
        self.update_model(
            "user/1",
            {
                "organization_management_level": None,
                "committee_$_management_level": [CommitteeManagementLevel.CAN_MANAGE],
                "committee_$can_manage_management_level": [1],
            },
        )
        status_code, data = self.request(
            "search_users_by_name_or_email",
            {
                "permission_type": UserScope.Meeting.value,
                "permission_id": 1,
                "search": [
                    {"username": "user2"},
                ],
            },
        )
        self.assertEqual(status_code, 200)

    def test_permission_meeting_via_committee_with_database_error(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        self.update_model(
            "user/1",
            {
                "organization_management_level": None,
                "committee_$_management_level": [CommitteeManagementLevel.CAN_MANAGE],
                "committee_$can_manage_management_level": [1],
            },
        )
        status_code, data = self.request(
            "search_users_by_name_or_email",
            {
                "permission_type": UserScope.Meeting.value,
                "permission_id": 1,
                "search": [
                    {"username": "user2"},
                ],
            },
        )
        self.assertEqual(status_code, 400)
        self.assertIn(
            "Error in database: Meeting 1 has no valid committee_id!", data["message"]
        )

    @performance
    def test_search_performance(self) -> None:
        quantity = 7000
        self.create_more_test_users(quantity=quantity)
        with Profiler("test_presenter_performance_search_users_by_name_or_email.prof"):
            status_code, data = self.request(
                "search_users_by_name_or_email",
                {
                    "permission_type": UserScope.Meeting.value,
                    "permission_id": 1,
                    "search": [
                        {
                            "username": "user2",
                        },
                        {
                            "email": "userX@test.de",
                        },
                        {
                            "username": "user2",
                            "email": "userX@test.de",
                        },
                        *[
                            {
                                "username": f"uSer{i}",
                                "email": "userX6@Test.de",
                            }
                            for i in range(5, 5 + quantity)
                        ],
                    ],
                },
            )
        self.assertEqual(status_code, 200)
        self.assertCountEqual(
            data["user2/"],
            [self.user2],
        )
        self.assertCountEqual(data.get(f"uSer{4+quantity}/", []), [])
        assert len(data[f"uSer{4+quantity}/userX6@Test.de"]) == 2
