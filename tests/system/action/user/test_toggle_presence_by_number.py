from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class UserTogglePresenceByNumberActionTest(BaseActionTestCase):
    def test_toggle_presence_by_number_add_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                "user/111": {
                    "username": "username_srtgb123",
                    "number_$1": "1",
                    "number_$": ["1"],
                },
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
                },
                "user/111": {
                    "username": "username_srtgb123",
                    "is_present_in_meeting_ids": [1],
                    "number_$1": "1",
                    "number_$": ["1"],
                },
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
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                "user/111": {
                    "username": "username_srtgb123",
                    "number_$1": "1",
                    "number_$": ["1"],
                },
                "user/112": {
                    "username": "username_srtgb235",
                    "number_$1": "1",
                    "number_$": ["1"],
                },
                "committee/1": {},
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

    def test_toggle_presence_by_number_too_many_default_numbers(self) -> None:
        self.set_models(
            {
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                "user/111": {
                    "username": "username_srtgb123",
                    "number_$1": "",
                    "number_$": ["1"],
                    "default_number": "1",
                },
                "user/112": {
                    "username": "username_srtgb235",
                    "number_$1": "",
                    "number_$": ["1"],
                    "default_number": "1",
                },
                "committee/1": {},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "1"}
        )
        self.assert_status_code(response, 400)
        assert (
            "Found more than one user with the default number."
            in response.json["message"]
        )

    def test_toggle_presence_by_number_other_user_default_number(self) -> None:
        self.set_models(
            {
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                "user/111": {
                    "username": "username_srtgb123",
                    "number_$1": "1",
                    "number_$": ["1"],
                },
                "user/112": {
                    "username": "username_srtgb123",
                    "number_$1": "",
                    "number_$": ["1"],
                    "default_number": "1",
                },
                "committee/1": {},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "1"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("is_present_in_meeting_ids") == [1]
        meeting = self.get_model("meeting/1")
        assert meeting.get("present_user_ids") == [111]
        model = self.get_model("user/112")
        assert model.get("is_present_in_meeting_ids") is None

    def test_toggle_presence_by_number_wrong_number_and_match_default_nuber(
        self,
    ) -> None:
        self.set_models(
            {
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                "user/111": {
                    "username": "username_srtgb123",
                    "number_$1": "1",
                    "number_$": ["1"],
                    "default_number": "2",
                },
                "committee/1": {},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "2"}
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
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                    "default_number": "test",
                    "number_$1": "",
                },
                "committee/1": {},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "test"}
        )
        self.assert_status_code(response, 200)

    def test_toggle_presence_by_number_committee_can_manage_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                "committee/1": {"user_ids": [1]},
                "user/1": {
                    "organization_management_level": None,
                    "committee_ids": [1],
                    "committee_$can_manage_management_level": [1],
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                    "number_$1": "",
                    "default_number": "test",
                },
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
                },
                "group/1": {
                    "user_ids": [1],
                    "permissions": [Permissions.User.CAN_MANAGE],
                },
                "user/1": {
                    "organization_management_level": None,
                    "group_$1_ids": [1],
                    "number_$1": "",
                    "default_number": "test",
                },
                "committee/1": {},
            }
        )
        response = self.request(
            "user.toggle_presence_by_number", {"meeting_id": 1, "number": "test"}
        )
        self.assert_status_code(response, 200)
