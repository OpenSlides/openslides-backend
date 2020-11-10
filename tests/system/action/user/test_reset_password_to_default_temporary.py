from tests.system.action.base import BaseActionTestCase


class UserResetPasswordToDefaultTemporaryTest(BaseActionTestCase):
    def test_reset_password_to_default_temporary(self) -> None:
        self.create_model("meeting/222", {"name": "name_meeting_222"})
        self.create_model(
            "user/111",
            {
                "username": "username_srtgb123",
                "default_password": "pw_quSEYapV",
                "meeting_id": 222,
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.reset_password_to_default_temporary",
                    "data": [{"id": 111}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert self.auth.is_equals("pw_quSEYapV", model.get("password", ""))

    def test_reset_temporary_non_temporary_user(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123", "default_password": "pw_quSEYapV"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.reset_password_to_default_temporary",
                    "data": [{"id": 111}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "User 111 is not temporary." in str(response.data)
