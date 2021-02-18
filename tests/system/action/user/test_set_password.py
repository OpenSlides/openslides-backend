from tests.system.action.base import BaseActionTestCase


class UserSetPasswordActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.update_model("user/1", {"password": "old_pw"})
        response = self.request("user.set_password", {"id": 1, "password": "test"})
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert self.auth.is_equals("test", model.get("password", ""))

    def test_update_correct_default_case(self) -> None:
        self.update_model("user/1", {"password": "old_pw"})
        response = self.request(
            "user.set_password", {"id": 1, "password": "test", "set_as_default": True}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert self.auth.is_equals("test", model.get("password", ""))
        assert "test" == model.get("default_password", "")
