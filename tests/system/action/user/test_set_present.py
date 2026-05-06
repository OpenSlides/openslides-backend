from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class UserSetPresentActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_set_present_add_correct(self) -> None:
        self.set_models(
            {
                "user/111": {"username": "username_srtgb123"},
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
                },
                "user/111": {
                    "username": "username_srtgb123",
                },
            }
        )
        response = self.request(
            "user.set_present", {"id": 111, "meeting_id": 1, "present": False}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/111", {"is_present_in_meeting_ids": None})
        self.assert_model_exists("meeting/1", {"present_user_ids": None})
        self.assert_history_information(
            "user/111", ["Set not present in meeting {}", "meeting/1"]
        )

    def test_set_present_null_action(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "present_user_ids": [],
                },
                "user/111": {
                    "username": "username_srtgb123",
                    "is_present_in_meeting_ids": [],
                },
            }
        )
        response = self.request(
            "user.set_present", {"id": 111, "meeting_id": 1, "present": False}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/111", {"is_present_in_meeting_ids": None})
        self.assert_model_exists("meeting/1", {"present_user_ids": None})

    def test_set_present_add_self_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_allow_self_set_present": True,
                },
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
                },
                "user/1": {"organization_management_level": None},
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
                },
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                },
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
                },
                "committee/60": {"manager_ids": [1]},
                "user/1": {
                    "organization_management_level": None,
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
                },
                "group/1": {
                    "meeting_user_ids": [1],
                    "permissions": [Permissions.User.CAN_MANAGE],
                },
                "user/1": {
                    "organization_management_level": None,
                },
                "meeting_user/1": {"meeting_id": 1, "user_id": 1},
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
                },
                "group/1": {
                    "meeting_user_ids": [1],
                    "permissions": [Permissions.User.CAN_MANAGE_PRESENCE],
                },
                "user/1": {
                    "organization_management_level": None,
                },
                "meeting_user/1": {"meeting_id": 1, "user_id": 1},
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
                },
                "user/1": {"organization_management_level": None},
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)

    def test_set_present_locked_meeting(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_allow_self_set_present": False,
                    "locked_from_inside": True,
                },
            }
        )
        self.set_user_groups(1, [3])
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to set present.",
            response.json["message"],
        )

    def test_set_present_cml_locked_meeting(
        self,
    ) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_allow_self_set_present": False,
                    "locked_from_inside": True,
                },
                "committee/60": {"manager_ids": [1]},
                "user/1": {
                    "organization_management_level": None,
                },
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to set present.",
            response.json["message"],
        )
