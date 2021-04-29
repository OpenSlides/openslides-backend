from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class UserResetPasswordToDefaultTemporaryTest(BaseActionTestCase):
    def test_reset_password_to_default_temporary(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_meeting_222"},
                "user/111": {
                    "username": "username_srtgb123",
                    "default_password": "pw_quSEYapV",
                    "meeting_id": 222,
                },
            }
        )
        response = self.request("user.reset_password_to_default_temporary", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equals("pw_quSEYapV", model.get("password", ""))

    def test_reset_temporary_non_temporary_user(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123", "default_password": "pw_quSEYapV"},
        )
        response = self.request("user.reset_password_to_default_temporary", {"id": 111})
        self.assert_status_code(response, 400)
        assert "User 111 in payload is not temporary." in response.json["message"]

    def test_reset_password_temporary_no_permissions(self) -> None:
        self.base_permission_test(
            {"user/10": {"username": "permission_test_user", "meeting_id": 1}},
            "user.reset_password_to_default_temporary",
            {"id": 10},
        )

    def test_reset_password_temporary_permissions(self) -> None:
        self.base_permission_test(
            {"user/10": {"username": "permission_test_user", "meeting_id": 1}},
            "user.reset_password_to_default_temporary",
            {"id": 10},
            Permissions.User.CAN_MANAGE,
        )
