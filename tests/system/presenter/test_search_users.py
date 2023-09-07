from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.filters import And, FilterOperator, Or
from openslides_backend.shared.mixins.user_scope_mixin import UserScope
from tests.system.util import Profiler, mock_datastore_method, performance

from .base import BasePresenterTestCase


class TestSearchUsers(BasePresenterTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user2 = {
            "id": 2,
            "email": "user2@test.de",
            "first_name": "first2",
            "last_name": "last2",
            "username": "user2",
            "saml_id": None,
        }
        self.user3 = {
            "id": 3,
            "email": "userX@test.de",
            "first_name": "first3",
            "last_name": "last3",
            "username": "user3",
            "saml_id": None,
        }
        self.user4 = {
            "id": 4,
            "email": "userX@test.de",
            "first_name": "first4",
            "last_name": "last4",
            "username": "user4",
            "saml_id": None,
        }
        self.user5 = {
            "id": 5,
            "email": "userX@test.de",
            "first_name": "first5",
            "last_name": "last5",
            "username": "user5",
            "saml_id": "saml5",
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
                "user/5": {
                    **self.user5,
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
            "search_users",
            {
                "permission_type": UserScope.Meeting,
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
                    {
                        "email": "userX@test.de",
                        "first_name": "first4",
                        "last_name": "last4",
                    },
                    {
                        "username": "user2",
                        "saml_id": "saml5",
                    },
                    {
                        "saml_id": "saml5",
                        "email": "userX@test.de",
                        "first_name": "first4",
                        "last_name": "last4",
                    },
                    {
                        "username": "userX",
                        "saml_id": "saml5",
                    },
                ],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(data), 7)
        self.assertEqual(data[0], [self.user2])
        self.assertEqual(data[1], [])
        self.assertEqual(data[2], [self.user2])
        self.assertEqual(data[3], [self.user4])
        self.assertEqual(data[4], [self.user2])
        self.assertEqual(data[5], [self.user5])
        self.assertEqual(data[6], [])

    def test_search_ignore_case_strip(self) -> None:
        status_code, data = self.request(
            "search_users",
            {
                "permission_type": UserScope.Meeting,
                "permission_id": 1,
                "search": [
                    {
                        "email": " User2@test.de ",
                        "first_name": " first2 ",
                        "last_name": "LAsT2   ",
                    },
                    {
                        "username": " USER2",
                    },
                ],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], [self.user2])
        self.assertEqual(data[1], [self.user2])

    def test_search_all_fields_username_match(self) -> None:
        status_code, data = self.request(
            "search_users",
            {
                "permission_type": UserScope.Meeting,
                "permission_id": 1,
                "search": [
                    {
                        "username": "user2",
                        "email": "userX@test.de",
                        "first_name": "first4",
                        "last_name": "last4",
                    },
                ],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], [self.user2])

    def test_search_all_fields_username_no_match(self) -> None:
        status_code, data = self.request(
            "search_users",
            {
                "permission_type": UserScope.Meeting,
                "permission_id": 1,
                "search": [
                    {
                        "username": "user42",
                        "email": "user2@test.de",
                        "first_name": "first2",
                        "last_name": "last2",
                    },
                ],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], [])

    def test_search_empty_username(self) -> None:
        status_code, data = self.request(
            "search_users",
            {
                "permission_type": UserScope.Meeting,
                "permission_id": 1,
                "search": [
                    {
                        "username": "",
                        "email": "user2@test.de",
                        "first_name": "first2",
                        "last_name": "last2",
                    },
                ],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], [self.user2])

    def test_search_empty_username_and_first_name(self) -> None:
        self.user2["first_name"] = ""
        self.update_model("user/2", self.user2)
        status_code, data = self.request(
            "search_users",
            {
                "permission_type": UserScope.Meeting,
                "permission_id": 1,
                "search": [
                    {
                        "username": "",
                        "email": "user2@test.de",
                        "first_name": "",
                        "last_name": "last2",
                    },
                ],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], [])

    def test_search_empty_username_and_first_name_is_none(self) -> None:
        self.user2["first_name"] = None
        self.update_model("user/2", self.user2)
        status_code, data = self.request(
            "search_users",
            {
                "permission_type": UserScope.Meeting,
                "permission_id": 1,
                "search": [
                    {
                        "username": "",
                        "email": "user2@test.de",
                        "first_name": "",
                        "last_name": "last2",
                    },
                ],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], [])

    def test_search_empty_username_and_email(self) -> None:
        self.user2["email"] = None
        self.update_model("user/2", self.user2)
        status_code, data = self.request(
            "search_users",
            {
                "permission_type": UserScope.Meeting,
                "permission_id": 1,
                "search": [
                    {
                        "username": "",
                        "email": "",
                        "first_name": "first2",
                        "last_name": "last2",
                    },
                ],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], [])

    def test_search_everything_empty(self) -> None:
        status_code, data = self.request(
            "search_users",
            {
                "permission_type": UserScope.Meeting,
                "permission_id": 1,
                "search": [
                    {
                        "username": "",
                        "email": "",
                        "first_name": "",
                        "last_name": "",
                    },
                ],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], [])

    def test_search_remove_duplicates(self) -> None:
        mock, patcher = mock_datastore_method("filter")
        status_code, data = self.request(
            "search_users",
            {
                "permission_type": UserScope.Meeting,
                "permission_id": 1,
                "search": [
                    {
                        "username": "user2",
                        "email": "user4@test.de",
                        "first_name": "first4",
                        "last_name": "last4",
                    },
                    {
                        "username": "user2",
                        "email": "user4@test.de",
                        "first_name": "first4",
                        "last_name": "last4",
                    },
                ],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], [self.user2])
        self.assertEqual(data[1], [self.user2])
        # assert only once in filter instead of twice
        self.assertEqual(
            mock.call_args[0][2],
            Or(And(Or(FilterOperator(field="username", operator="~=", value="user2")))),
        )
        patcher.stop()

    def test_search_wrong_permission_type(self) -> None:
        status_code, data = self.request(
            "search_users",
            {
                "permission_type": "user",
                "permission_id": 1,
                "search": [
                    {"username": "user2"},
                ],
            },
        )
        self.assertEqual(status_code, 400)
        self.assertIn(
            "data.permission_type must be one of ['meeting', 'committee', 'organization']",
            data["message"],
        )

    def test_search_wrong_permission_id(self) -> None:
        status_code, data = self.request(
            "search_users",
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
            "search_users",
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
            "search_users",
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
                "committee_management_ids": [1],
            },
        )
        status_code, _ = self.request(
            "search_users",
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
            "search_users",
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
                    "meeting_user_ids": [1],
                    "meeting_id": 1,
                    "permissions": [Permissions.User.CAN_MANAGE],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [1],
                },
            }
        )
        self.update_model(
            "user/1",
            {
                "organization_management_level": None,
            },
        )
        status_code, _ = self.request(
            "search_users",
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
            "search_users",
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
                "committee_management_ids": [1],
            },
        )
        status_code, data = self.request(
            "search_users",
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
                "committee_management_ids": [1],
            },
        )
        status_code, data = self.request(
            "search_users",
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
        with Profiler("test_presenter_performance_search_users.prof"):
            status_code, data = self.request(
                "search_users",
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
