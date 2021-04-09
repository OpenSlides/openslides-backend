from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class UserDeleteTemporaryActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {"temporary_user_ids": [111], "user_ids": [111]},
                "user/111": {"username": "username_srtgb123", "meeting_id": 1},
            }
        )
        response = self.request("user.delete_temporary", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")
        meeting = self.get_model("meeting/1")
        assert meeting.get("temporary_user_ids") == []
        assert meeting.get("user_ids") == []

    def test_delete_not_temporary(self) -> None:
        self.create_model("user/111", {"username": "username_srtgb123"})
        response = self.request("user.delete_temporary", {"id": 111})

        self.assert_status_code(response, 400)
        self.assertIn("User 111 in payload is not temporary.", response.json["message"])
        self.assert_model_exists("user/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("user/112", {"username": "username_srtgb123"})
        response = self.request("user.delete_temporary", {"id": 111})
        self.assert_status_code(response, 400)
        model = self.get_model("user/112")
        assert model.get("username") == "username_srtgb123"

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            {"user/10": {"username": "permission_test_user", "meeting_id": 1}},
            "user.delete_temporary",
            {"id": 10},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {"user/10": {"username": "permission_test_user", "meeting_id": 1}},
            "user.delete_temporary",
            {"id": 10},
            Permissions.User.CAN_MANAGE,
        )
