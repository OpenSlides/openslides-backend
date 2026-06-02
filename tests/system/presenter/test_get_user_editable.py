from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions

from .base import BasePresenterTestCase


class TestGetUSerEditable(BasePresenterTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user111 = {
            "user/111": {
                "username": "Helmhut",
                "last_name": "Schmidt",
                "is_active": True,
                "password": self.auth.hash("Kohl"),
                "default_password": "Kohl",
            }
        }
        self.data: dict[str, dict[str, Any]] = {
            **self.user111,
            "user/2": {
                "username": "only_oml_level",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
            "user/3": {"username": "only_cml_level"},
            "user/4": {"username": "cml_and_meeting"},
            "user/5": {"username": "no_organization"},
            "user/6": {
                "username": "oml_and_meeting",
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
            },
            "user/7": {"username": "meeting_and_archived_meeting"},
            "committee/60": {"manager_ids": [4]},
            "committee/63": {"manager_ids": [3]},
            "meeting_user/14": {"meeting_id": 1, "user_id": 4},
            "meeting_user/16": {"meeting_id": 1, "user_id": 6},
            "meeting_user/17": {"meeting_id": 1, "user_id": 7},
            "meeting_user/47": {"meeting_id": 4, "user_id": 7},
            "group/1": {"meeting_user_ids": [14, 16, 17]},
            "group/4": {"meeting_user_ids": [47]},
        }

    def set_up(self) -> None:
        self.create_meeting(1)
        self.create_meeting(
            4,
            {
                "committee_id": 60,
                "is_active_in_organization_id": None,
                "is_archived_in_organization_id": 1,
            },
        )
        self.set_models(self.data)
        self.login(111)

    def test_with_oml(self) -> None:
        self.data["user/111"][
            "organization_management_level"
        ] = OrganizationManagementLevel.CAN_MANAGE_USERS
        self.set_up()
        status_code, data = self.request(
            "get_user_editable",
            {
                "user_ids": [2, 3, 4, 5, 6, 7],
                "fields": ["first_name", "default_password"],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            {
                "2": {
                    "default_password": [True, ""],
                    "first_name": [True, ""],
                },
                "3": {
                    "default_password": [True, ""],
                    "first_name": [True, ""],
                },
                "4": {
                    "default_password": [True, ""],
                    "first_name": [True, ""],
                },
                "5": {
                    "default_password": [True, ""],
                    "first_name": [True, ""],
                },
                "6": {
                    "default_password": [
                        False,
                        "Your organization management level is not high enough to change a user with a Level of superadmin!",
                    ],
                    "first_name": [
                        False,
                        "Your organization management level is not high enough to change a user with a Level of superadmin!",
                    ],
                },
                "7": {
                    "default_password": [True, ""],
                    "first_name": [True, ""],
                },
            },
        )

    def test_with_cml(self) -> None:
        self.data["committee/60"]["manager_ids"] = [111, 4]
        self.set_up()
        status_code, data = self.request(
            "get_user_editable",
            {
                "user_ids": [2, 3, 4, 5, 6, 7],
                "fields": ["first_name", "default_password"],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            {
                "2": {
                    "default_password": [
                        False,
                        "Your organization management level is not high enough to change a user with a Level of can_manage_users!",
                    ],
                    "first_name": [
                        False,
                        "Your organization management level is not high enough to change a user with a Level of can_manage_users!",
                    ],
                },
                "3": {
                    "default_password": [
                        False,
                        "Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 63",
                    ],
                    "first_name": [
                        False,
                        "Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 63",
                    ],
                },
                "4": {
                    "default_password": [True, ""],
                    "first_name": [True, ""],
                },
                "5": {
                    "default_password": [
                        False,
                        "Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
                    ],
                    "first_name": [
                        False,
                        "Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
                    ],
                },
                "6": {
                    "default_password": [
                        False,
                        "Your organization management level is not high enough to change a user with a Level of superadmin!",
                    ],
                    "first_name": [
                        False,
                        "Your organization management level is not high enough to change a user with a Level of superadmin!",
                    ],
                },
                "7": {
                    "default_password": [True, ""],
                    "first_name": [True, ""],
                },
            },
        )

    def test_with_same_meeting(self) -> None:
        """
        User 5 can be edited because he is only in meetings which User 111 is admin of.
        User 7 can not be edited because he is in two of the same meetings but User 111 is not admin in all of them.
        """
        self.set_models(
            {
                **self.user111,
                "user/5": {"username": "user5"},
                "user/7": {"username": "user7"},
            }
        )

        self.create_meeting_for_two_users(1, 5, 111)
        self.create_meeting_for_two_users(4, 5, 111)
        self.create_meeting_for_two_users(7, 7, 111, {"committee_id": 60})
        self.create_meeting_for_two_users(10, 7, 111, {"committee_id": 66})

        # User 111 is meeting admin in meeting 1, 4 and 7 but normal user in 10
        # User 5 is normal user in meeting 1 and 4
        # User 7 is normal user in meeting 7 and 10
        self.move_users_to_groups(
            {
                111: [2, 5, 8, 10],
                5: [1, 4],
                7: [7, 10],
            }
        )
        self.login(111)

        status_code, data = self.request(
            "get_user_editable",
            {
                "user_ids": [5, 7],
                "fields": ["first_name", "default_password"],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            {
                "5": {"default_password": [True, ""], "first_name": [True, ""]},
                "7": {
                    "default_password": [
                        False,
                        "Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meetings {10, 7}",
                    ],
                    "first_name": [
                        False,
                        "Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meetings {10, 7}",
                    ],
                },
            },
        )

    def test_with_same_meeting_can_update(self) -> None:
        """
        User 5 can be edited because he is only in meetings which User 111 has can_manage of.
        User 7 can be edited because he is only in meetings which User 111 has can_update of.
        """
        self.set_models(
            {
                **self.user111,
                "user/5": {"username": "user5"},
                "user/7": {"username": "user7"},
            }
        )

        self.create_meeting_for_two_users(1, 5, 111)
        self.create_meeting_for_two_users(4, 5, 111)
        self.create_meeting_for_two_users(7, 7, 111, {"committee_id": 60})
        self.create_meeting_for_two_users(10, 7, 111, {"committee_id": 66})
        self.set_group_permissions(3, [Permissions.User.CAN_UPDATE])
        self.set_group_permissions(6, [Permissions.User.CAN_UPDATE])
        self.set_group_permissions(9, [Permissions.User.CAN_MANAGE])
        self.set_group_permissions(12, [Permissions.User.CAN_MANAGE])
        # User 111 has sufficient group rights in meeting 1, 4, 7 and 10
        # User 5 is normal user in meeting 1 and 4
        # User 7 is normal user in meeting 7 and 10
        self.move_users_to_groups(
            {
                111: [3, 6, 9, 12],
                5: [1, 4],
                7: [7, 10],
            }
        )
        self.login(111)
        status_code, data = self.request(
            "get_user_editable",
            {
                "user_ids": [5, 7],
                "fields": ["first_name", "default_password"],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            {
                "5": {"default_password": [True, ""], "first_name": [True, ""]},
                "7": {"default_password": [True, ""], "first_name": [True, ""]},
            },
        )

    def test_with_all_payload_groups(self) -> None:
        """
        Tests all user.create/update payload field groups. Especially the field 'saml_id'.
        """
        self.data["user/111"][
            "organization_management_level"
        ] = OrganizationManagementLevel.CAN_MANAGE_USERS
        self.set_up()
        status_code, data = self.request(
            "get_user_editable",
            {
                "user_ids": [2, 3, 4, 5, 6, 7],
                "fields": [
                    "first_name",
                    "default_password",
                    "vote_weight",
                    "group_ids",
                    "committee_management_ids",
                    "organization_management_level",
                    "is_demo_user",
                    "saml_id",
                ],
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            {
                "2": {
                    "committee_management_ids": [True, ""],
                    "default_password": [True, ""],
                    "first_name": [True, ""],
                    "group_ids": [True, ""],
                    "is_demo_user": [
                        False,
                        "Missing OrganizationManagementLevel: superadmin",
                    ],
                    "organization_management_level": [True, ""],
                    "saml_id": [
                        False,
                        "The field 'saml_id' can only be used in internal action calls",
                    ],
                    "vote_weight": [True, ""],
                },
                "3": {
                    "committee_management_ids": [True, ""],
                    "default_password": [True, ""],
                    "first_name": [True, ""],
                    "group_ids": [True, ""],
                    "is_demo_user": [
                        False,
                        "Missing OrganizationManagementLevel: superadmin",
                    ],
                    "organization_management_level": [True, ""],
                    "saml_id": [
                        False,
                        "The field 'saml_id' can only be used in internal action calls",
                    ],
                    "vote_weight": [True, ""],
                },
                "4": {
                    "committee_management_ids": [True, ""],
                    "default_password": [True, ""],
                    "first_name": [True, ""],
                    "group_ids": [True, ""],
                    "is_demo_user": [
                        False,
                        "Missing OrganizationManagementLevel: superadmin",
                    ],
                    "organization_management_level": [True, ""],
                    "saml_id": [
                        False,
                        "The field 'saml_id' can only be used in internal action calls",
                    ],
                    "vote_weight": [True, ""],
                },
                "5": {
                    "committee_management_ids": [True, ""],
                    "default_password": [True, ""],
                    "first_name": [True, ""],
                    "group_ids": [True, ""],
                    "is_demo_user": [
                        False,
                        "Missing OrganizationManagementLevel: superadmin",
                    ],
                    "organization_management_level": [True, ""],
                    "saml_id": [
                        False,
                        "The field 'saml_id' can only be used in internal action calls",
                    ],
                    "vote_weight": [True, ""],
                },
                "6": {
                    "committee_management_ids": [
                        False,
                        "Your organization management level is not high enough to change a user with a Level of superadmin!",
                    ],
                    "default_password": [
                        False,
                        "Your organization management level is not high enough to change a user with a Level of superadmin!",
                    ],
                    "first_name": [
                        False,
                        "Your organization management level is not high enough to change a user with a Level of superadmin!",
                    ],
                    "group_ids": [True, ""],
                    "is_demo_user": [
                        False,
                        "Your organization management level is not high enough to change a user with a Level of superadmin!",
                    ],
                    "organization_management_level": [
                        False,
                        "Your organization management level is not high enough to change a user with a Level of superadmin!",
                    ],
                    "saml_id": [
                        False,
                        "Your organization management level is not high enough to change a user with a Level of superadmin!",
                    ],
                    "vote_weight": [True, ""],
                },
                "7": {
                    "committee_management_ids": [True, ""],
                    "default_password": [True, ""],
                    "first_name": [True, ""],
                    "group_ids": [True, ""],
                    "is_demo_user": [
                        False,
                        "Missing OrganizationManagementLevel: superadmin",
                    ],
                    "organization_management_level": [True, ""],
                    "saml_id": [
                        False,
                        "The field 'saml_id' can only be used in internal action calls",
                    ],
                    "vote_weight": [True, ""],
                },
            },
        )

    def test_payload_list_of_None(self) -> None:
        status_code, data = self.request(
            "get_user_editable",
            {
                "user_ids": [None],
                "fields": [
                    "first_name",
                    "default_password",
                ],
            },
        )
        self.assertEqual(status_code, 400)
        self.assertIn("data.user_ids[0] must be integer", data["message"])
        status_code, data = self.request(
            "get_user_editable", {"user_ids": [1, 2], "fields": [None]}
        )
        self.assertEqual(status_code, 400)
        self.assertIn("data.fields[0] must be string", data["message"])

    def test_payload_empty_list(self) -> None:
        status_code, data = self.request(
            "get_user_editable",
            {
                "user_ids": [],
                "fields": [
                    "first_name",
                    "default_password",
                ],
            },
        )
        self.assertEqual(status_code, 200)
        assert data == {}
        status_code, data = self.request(
            "get_user_editable", {"user_ids": [1, 2], "fields": []}
        )
        self.assertEqual(status_code, 400)
        assert data == {
            "message": "Need at least one field name to check editability.",
            "success": False,
        }
