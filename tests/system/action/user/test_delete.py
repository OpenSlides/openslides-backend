from openslides_backend.permissions.permissions import OrganisationManagementLevel
from tests.system.action.base import BaseActionTestCase


class UserDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("user/111", {"username": "username_srtgb123"})
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("user/112", {"username": "username_srtgb123"})
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 400)
        model = self.get_model("user/112")
        assert model.get("username") == "username_srtgb123"

    def test_delete_correct_with_template_field(self) -> None:
        self.set_models(
            {
                "user/111": {
                    "username": "username_srtgb123",
                    "group_$_ids": ["42"],
                    "group_$42_ids": [456],
                },
                "group/456": {"meeting_id": 42, "user_ids": [111, 222]},
                "meeting/42": {"group_ids": [456], "user_ids": [111]},
            }
        )
        response = self.request("user.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")
        model = self.get_model("group/456")
        assert model.get("user_ids") == [222]
        # check meeting.user_ids
        meeting = self.get_model("meeting/42")
        assert meeting.get("user_ids") == []

    def test_delete_no_permission(self) -> None:
        self.update_model("user/1", {"organisation_management_level": None})
        self.create_model("user/111", {"username": "username_srtgb123"})
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.delete. Missing permission: can_manage_users",
            response.json["message"],
        )

    def test_delete_permission(self) -> None:
        self.update_model(
            "user/1",
            {
                "organisation_management_level": OrganisationManagementLevel.CAN_MANAGE_USERS
            },
        )
        self.create_model("user/111", {"username": "username_srtgb123"})
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")

    def test_delete_temporary_user(self) -> None:
        self.create_meeting()
        self.update_model(
            "user/1",
            {
                "organisation_management_level": OrganisationManagementLevel.CAN_MANAGE_USERS
            },
        )
        self.create_model(
            "user/111", {"username": "username_srtgb123", "meeting_id": 1}
        )
        response = self.request("user.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 111 in payload may not be a temporary user.",
            response.json["message"],
        )
        self.assert_model_exists("user/111")
