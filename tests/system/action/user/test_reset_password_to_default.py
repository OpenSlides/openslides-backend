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
