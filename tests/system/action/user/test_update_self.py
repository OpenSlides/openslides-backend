from tests.system.action.base import BaseActionTestCase


class UserUpdateSelfActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.update_model(
            "user/1",
            {"username": "username_srtgb123"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update_self",
                    "data": [
                        {
                            "username": "username_Xcdfgee",
                            "email": "email1@example.com",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert model.get("username") == "username_Xcdfgee"
        assert model.get("email") == "email1@example.com"
