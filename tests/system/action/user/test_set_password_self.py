from tests.system.action.base import BaseActionTestCase


class UserUpdateSelfActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        old_hash = self.auth.hash("old")
        self.update_model(
            "user/1",
            {"password": old_hash},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.set_password_self",
                    "data": [{"old_password": "old", "new_password": "new"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert model.get("old_password") is None
        assert model.get("new_password") is None
        assert self.auth.is_equals("new", model.get("password", ""))

    def test_update_wrong_password(self) -> None:
        old_hash = self.auth.hash("old")
        self.update_model(
            "user/1",
            {"password": old_hash},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.set_password_self",
                    "data": [{"old_password": "wrong", "new_password": "new"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("user/1")
        assert model.get("password") == old_hash
