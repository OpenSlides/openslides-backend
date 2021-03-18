from tests.system.action.base import BaseActionTestCase


class UserUpdateSelfActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.update_model(
            "user/1",
            {"username": "username_srtgb123"},
        )
        response = self.request(
            "user.update_self",
            {
                "username": "username_Xcdfgee",
                "email": "email1@example.com",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert model.get("username") == "username_Xcdfgee"
        assert model.get("email") == "email1@example.com"

    def test_username_already_given(self) -> None:
        self.create_model("user/222", {"username": "user"})
        response = self.request("user.update_self", {"username": "user"})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"] == "A user with the username user already exists."
        )
