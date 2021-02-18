from tests.system.action.base import BaseActionTestCase


class UserGenerateNewPaswordActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.update_model("user/1", {"password": "old_pw"})
        response = self.request("user.generate_new_password", {"id": 1})
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert model.get("password") is not None
        assert self.auth.is_equals(
            model.get("default_password", ""), model.get("password", "")
        )
