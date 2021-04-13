from openslides_backend.permissions.permissions import OrganisationManagementLevel
from tests.system.action.base import BaseActionTestCase


class UserResetPasswordToDefaultTest(BaseActionTestCase):
    def test_reset_password_to_default(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123", "default_password": "pw_quSEYapV"},
        )
        response = self.request("user.reset_password_to_default", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equals("pw_quSEYapV", str(model.get("password")))

    def test_update_temporary(self) -> None:
        self.update_model("user/1", {"meeting_id": 1})
        response = self.request("user.reset_password_to_default", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 1 in payload may not be a temporary user.", response.json["message"]
        )

    def test_generate_no_permissions(self) -> None:
        self.base_permission_test(
            {"user/10": {"username": "permission_test_user"}},
            "user.reset_password_to_default",
            {"id": 10},
        )

    def test_generate_permissions(self) -> None:
        self.base_permission_test(
            {"user/10": {"username": "permission_test_user"}},
            "user.reset_password_to_default",
            {"id": 10},
            OrganisationManagementLevel.CAN_MANAGE_USERS,
        )
