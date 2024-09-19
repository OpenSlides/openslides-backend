from openslides_backend.permissions.management_levels import OrganizationManagementLevel

from .base import BasePresenterTestCase


class TestGetUSerEditable(BasePresenterTestCase):
    def set_up(self) -> None:
        self.create_model(
            "user/111",
            {
                "username": "Helmhut",
                "last_name": "Schmidt",
                "is_active": True,
                "password": self.auth.hash("Kohl"),
                "default_password": "Kohl",
            },
        )
        self.login(111)
        self.set_models(
            {
                "meeting/1": {
                    "committee_id": 2,
                    "is_active_in_organization_id": 1,
                },
                # archived meeting
                "meeting/2": {
                    "committee_id": 2,
                    "is_active_in_organization_id": None,
                    "is_archived_in_organization_id": 1,
                },
                "committee/1": {},
                "committee/2": {"meeting_ids": [1, 2]},
                "user/2": {
                    "username": "only_oml_level",
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                },
                "user/3": {
                    "username": "only_cml_level",
                    "committee_management_ids": [1],
                    "meeting_ids": [],
                },
                "user/4": {
                    "username": "cml_and_meeting",
                    "meeting_ids": [1],
                    "committee_management_ids": [2],
                },
                "user/5": {
                    "username": "no_organization",
                    "meeting_ids": [],
                },
                "user/6": {
                    "username": "oml_and_meeting",
                    "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                    "meeting_ids": [1],
                },
                "user/7": {
                    "username": "meeting_and_archived_meeting",
                    "meeting_ids": [1, 2],
                },
            }
        )

    def test_with_oml(self) -> None:
        self.set_up()
        self.update_model(
            "user/111",
            {
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
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
                    "editable": True,
                },
                "3": {
                    "editable": True,
                },
                "4": {
                    "editable": True,
                },
                "5": {
                    "editable": True,
                },
                "6": {
                    "editable": False,
                    "message": "Your organization management level is not high enough to change a user with a Level of superadmin!",
                },
                "7": {
                    "editable": True,
                },
            },
        )

    def test_with_cml(self) -> None:
        self.set_up()
        self.update_model(
            "user/111",
            {
                "committee_management_ids": [2],
            },
        )
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
                    "editable": False,
                    "message": "Your organization management level is not high enough to change a user with a Level of can_manage_users!",
                },
                "3": {
                    "editable": False,
                    "message": "Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 1",
                },
                "4": {
                    "editable": True,
                },
                "5": {
                    "editable": False,
                    "message": "Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
                },
                "6": {
                    "editable": False,
                    "message": "Your organization management level is not high enough to change a user with a Level of superadmin!",
                },
                "7": {
                    "editable": True,
                },
            },
        )

    def test_with_same_meeting(self) -> None:
        """
        User 5 can be edited because he is only in meetings which User 111 is admin of.
        User 7 can not be edited because he is in two of the same meetings but User 111 is not admin in all of them.
        """
        self.set_up()
        self.create_meeting_for_two_users(5, 111, 1)
        self.create_meeting_for_two_users(5, 111, 4)
        self.create_meeting_for_two_users(7, 111, 7)
        self.create_meeting_for_two_users(7, 111, 10)
        self.update_model("meeting/1", {"committee_id": 1})
        self.update_model("meeting/4", {"committee_id": 2})
        self.update_model("meeting/7", {"committee_id": 1})
        self.update_model("meeting/10", {"committee_id": 2})
        # User 111 is meeting admin in meeting 1, 4 and 7 but normal user in 10
        # User 5 is normal user in meeting 1 and 4
        # User 7 is normal user in meeting 7 and 10
        meeting_user_to_group = {
            1111: 2,
            4111: 5,
            15: 1,
            45: 4,
            7111: 8,
            10111: 10,
            77: 7,
            107: 10,
        }
        self.move_user_to_group(meeting_user_to_group)
        self.update_model(
            "user/5",
            {
                "meeting_user_ids": [
                    15,
                    45,
                ],
                "meeting_ids": [1, 4],
            },
        )
        self.update_model(
            "user/7",
            {
                "meeting_user_ids": [77, 107],
                "meeting_ids": [7, 10],
            },
        )
        self.update_model(
            "user/111",
            {
                "meeting_user_ids": [1111, 4111, 7111, 10111],
                "meeting_ids": [1, 4, 7, 10],
            },
        )
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
                "5": {
                    "editable": True,
                },
                "7": {
                    "editable": False,
                    "message": "Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 7",
                },
            },
        )

    def test_with_all_payload_groups(self) -> None:
        """
        Tests all user.create/update payload field groups. Especially the field 'saml_id'.
        """
        self.set_up()
        self.update_model(
            "user/111",
            {
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
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
                    "editable": False,
                    "message": "The field 'saml_id' can only be used in internal action calls",
                },
                "3": {
                    "editable": False,
                    "message": "The field 'saml_id' can only be used in internal action calls",
                },
                "4": {
                    "editable": False,
                    "message": "The field 'saml_id' can only be used in internal action calls",
                },
                "5": {
                    "editable": False,
                    "message": "The field 'saml_id' can only be used in internal action calls",
                },
                "6": {
                    "editable": False,
                    "message": "Your organization management level is not high enough to change a user with a Level of superadmin!",
                },
                "7": {
                    "editable": False,
                    "message": "The field 'saml_id' can only be used in internal action calls",
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
