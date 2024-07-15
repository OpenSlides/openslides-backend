from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class UserSetPresentActionTest(BaseActionTestCase):
    def test_set_present_add_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "Test Meeting",
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "user/111": {"username": "username_srtgb123"},
                "committee/1": {},
            }
        )
        response = self.request(
            "user.set_present", {"id": 111, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("is_present_in_meeting_ids") == [1]
        meeting = self.get_model("meeting/1")
        assert meeting.get("present_user_ids") == [111]
        self.assert_history_information(
            "user/111", ["Set present in meeting {}", "meeting/1"]
        )

    def test_set_present_del_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "present_user_ids": [111],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "user/111": {
                    "username": "username_srtgb123",
                    "is_present_in_meeting_ids": [1],
                },
                "committee/1": {},
            }
        )
        response = self.request(
            "user.set_present", {"id": 111, "meeting_id": 1, "present": False}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("is_present_in_meeting_ids") == []
        meeting = self.get_model("meeting/1")
        assert meeting.get("present_user_ids") == []
        self.assert_history_information(
            "user/111", ["Set not present in meeting {}", "meeting/1"]
        )

    def test_set_present_null_action(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "present_user_ids": [],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "user/111": {
                    "username": "username_srtgb123",
                    "is_present_in_meeting_ids": [],
                },
                "committee/1": {},
            }
        )
        response = self.request(
            "user.set_present", {"id": 111, "meeting_id": 1, "present": False}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("is_present_in_meeting_ids") == []
        meeting = self.get_model("meeting/1")
        assert meeting.get("present_user_ids") == []

    def test_set_present_add_self_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_allow_self_set_present": True,
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "committee/1": {},
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert model.get("is_present_in_meeting_ids") == [1]
        meeting = self.get_model("meeting/1")
        assert meeting.get("present_user_ids") == [1]

    def test_set_present_no_permissions(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_allow_self_set_present": False,
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "user/1": {"organization_management_level": None},
                "committee/1": {},
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 403)

    def test_set_present_orga_can_manage_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_allow_self_set_present": False,
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                },
                "committee/1": {},
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)

    def test_set_present_committee_can_manage_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_allow_self_set_present": False,
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "committee/1": {"user_ids": [1]},
                "user/1": {
                    "organization_management_level": None,
                    "committee_ids": [1],
                    "committee_management_ids": [1],
                },
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)

    def test_set_present_meeting_can_manage_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_allow_self_set_present": False,
                    "group_ids": [1],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [1],
                },
                "group/1": {
                    "meeting_user_ids": [1],
                    "permissions": [Permissions.User.CAN_MANAGE],
                },
                "user/1": {
                    "organization_management_level": None,
                    "meeting_user_ids": [1],
                },
                "meeting_user/1": {"meeting_id": 1, "user_id": 1, "group_ids": [1]},
                "committee/1": {},
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)

    def test_set_present_meeting_can_manage_presence_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_allow_self_set_present": False,
                    "group_ids": [1],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [1],
                },
                "group/1": {
                    "meeting_user_ids": [1],
                    "permissions": [Permissions.User.CAN_MANAGE_PRESENCE],
                },
                "user/1": {
                    "organization_management_level": None,
                    "meeting_user_ids": [1],
                },
                "meeting_user/1": {"meeting_id": 1, "user_id": 1, "group_ids": [1]},
                "committee/1": {},
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)

    def test_set_present_self_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_allow_self_set_present": True,
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "user/1": {"organization_management_level": None},
                "committee/1": {},
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)

    def test_set_present_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "meeting/1": {
                    "users_allow_self_set_present": False,
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "committee/1": {},
            },
            "user.set_present",
            {"id": 1, "meeting_id": 1, "present": True},
        )
