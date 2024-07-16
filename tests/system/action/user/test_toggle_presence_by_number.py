from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class UserTogglePresenceByNumberActionTest(BaseActionTestCase):
    def test_toggle_presence_by_number_add_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [34],
                },
                "user/111": {
                    "username": "username_srtgb123",
                    "meeting_user_ids": [34],
                },
                "meeting_user/34": {"user_id": 111, "meeting_id": 1, "number": "1"},
                "committee/1": {},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "1"}
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["id"] == 111
        model = self.get_model("user/111")
        assert model.get("is_present_in_meeting_ids") == [1]
        meeting = self.get_model("meeting/1")
        assert meeting.get("present_user_ids") == [111]

    def test_toggle_presence_by_number_del_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "present_user_ids": [111],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [34],
                },
                "user/111": {
                    "username": "username_srtgb123",
                    "is_present_in_meeting_ids": [1],
                    "meeting_user_ids": [34],
                },
                "meeting_user/34": {"user_id": 111, "meeting_id": 1, "number": "1"},
                "committee/1": {},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "1"}
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["id"] == 111
        model = self.get_model("user/111")
        assert model.get("is_present_in_meeting_ids") == []
        meeting = self.get_model("meeting/1")
        assert meeting.get("present_user_ids") == []

    def test_toggle_presence_by_number_too_many_numbers(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [34, 35],
                },
                "user/111": {
                    "username": "username_srtgb123",
                    "meeting_user_ids": [34],
                },
                "user/112": {
                    "username": "username_srtgb235",
                    "meeting_user_ids": [35],
                },
                "committee/1": {},
                "meeting_user/34": {"user_id": 111, "meeting_id": 1, "number": "1"},
                "meeting_user/35": {"user_id": 112, "meeting_id": 1, "number": "1"},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "1"}
        )
        self.assert_status_code(response, 400)
        assert "Found more than one user with the number." in response.json["message"]

    def test_toggle_presence_by_number_no_number(self) -> None:
        self.set_models(
            {
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                "committee/1": {},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "1"}
        )
        self.assert_status_code(response, 400)
        assert "No user with this number found." in response.json["message"]

    def test_toggle_presence_by_number_no_permissions(self) -> None:
        self.set_models(
            {
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                "user/1": {"organization_management_level": None},
                "committee/1": {},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "test"}
        )
        self.assert_status_code(response, 403)

    def test_toggle_presence_by_number_orga_can_manage_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [34],
                },
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                    "meeting_user_ids": [34],
                },
                "committee/1": {},
                "meeting_user/34": {"user_id": 1, "meeting_id": 1, "number": "test"},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "test"}
        )
        self.assert_status_code(response, 200)

    def test_toggle_presence_by_number_committee_can_manage_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [34],
                },
                "committee/1": {"user_ids": [1]},
                "user/1": {
                    "organization_management_level": None,
                    "committee_ids": [1],
                    "committee_management_ids": [1],
                    "meeting_user_ids": [34],
                },
                "meeting_user/34": {"user_id": 1, "meeting_id": 1, "number": "test"},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "test"}
        )
        self.assert_status_code(response, 200)

    def test_toggle_presence_by_number_meeting_can_manage_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "group_ids": [1],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [34],
                },
                "group/1": {
                    "meeting_user_ids": [1],
                    "permissions": [Permissions.User.CAN_MANAGE],
                },
                "user/1": {
                    "organization_management_level": None,
                    "meeting_user_ids": [34],
                },
                "meeting_user/34": {
                    "user_id": 1,
                    "meeting_id": 1,
                    "number": "test",
                    "group_ids": [1],
                },
                "committee/1": {},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "test"}
        )
        self.assert_status_code(response, 200)

    def test_toggle_presence_by_number_meeting_can_update_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "group_ids": [1],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [34],
                },
                "group/1": {
                    "meeting_user_ids": [1],
                    "permissions": [Permissions.User.CAN_UPDATE],
                },
                "user/1": {
                    "organization_management_level": None,
                    "meeting_user_ids": [34],
                },
                "meeting_user/34": {
                    "user_id": 1,
                    "meeting_id": 1,
                    "number": "test",
                    "group_ids": [1],
                },
                "committee/1": {},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "test"}
        )
        self.assert_status_code(response, 200)

    def test_toggle_presence_by_number_locked_meeting(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [34],
                    "locked_from_inside": True,
                },
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                    "meeting_user_ids": [34],
                },
                "committee/1": {},
                "meeting_user/34": {"user_id": 1, "meeting_id": 1, "number": "test"},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "test"}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to toggle presence by number.",
            response.json["message"],
        )

    def test_toggle_presence_by_number_cml_locked_meeting(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [34],
                    "locked_from_inside": True,
                },
                "committee/1": {"user_ids": [1]},
                "user/1": {
                    "organization_management_level": None,
                    "committee_ids": [1],
                    "committee_management_ids": [1],
                    "meeting_user_ids": [34],
                },
                "meeting_user/34": {"user_id": 1, "meeting_id": 1, "number": "test"},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "test"}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to toggle presence by number.",
            response.json["message"],
        )
