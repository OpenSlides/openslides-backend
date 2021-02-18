from tests.system.action.base import BaseActionTestCase


class UserSetPasswordTemporaryActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/2": {"name": "name_meeting_2"},
                "user/1": {"password": "old_pw", "meeting_id": 2},
            }
        )
        response = self.request(
            "user.set_password_temporary", {"id": 1, "password": "test"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert self.auth.is_equals("test", model.get("password", ""))

    def test_update_correct_default_case(self) -> None:
        self.set_models(
            {
                "meeting/2": {"name": "meeting_2"},
                "user/1": {"password": "old_pw", "meeting_id": 2},
            }
        )
        response = self.request(
            "user.set_password_temporary",
            {"id": 1, "password": "test", "set_as_default": True},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert self.auth.is_equals("test", model.get("password", ""))
        assert "test" == model.get("default_password")

    def test_update_not_temporary_user(self) -> None:
        self.update_model("user/1", {"password": "old_pw"})
        response = self.request(
            "user.set_password_temporary",
            {"id": 1, "password": "test", "set_as_default": True},
        )
        self.assert_status_code(response, 400)
        self.assertIn("User 1 is not temporary.", response.json["message"])
