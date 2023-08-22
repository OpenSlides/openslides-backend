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
                "email": " email1@example.com   ",
                "pronoun": "Test",
                "gender": "male",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert model.get("username") == "username_Xcdfgee"
        assert model.get("email") == "email1@example.com"
        assert model.get("pronoun") == "Test"
        assert model.get("gender") == "male"
        self.assert_history_information("user/1", ["Personal data changed"])

    def test_username_already_given(self) -> None:
        self.create_model("user/222", {"username": "user"})
        response = self.request("user.update_self", {"username": "user"})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"] == "A user with the username user already exists."
        )

    def test_update_self_anonymus(self) -> None:
        response = self.request(
            "user.update_self",
            {"email": "user@openslides.org"},
            anonymous=True,
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Anonymous is not allowed to execute user.update_self",
            response.json["message"],
        )

    def test_update_self_forbidden_username(self) -> None:
        self.update_model(
            "user/1",
            {"username": "username_srtgb123"},
        )
        response = self.request(
            "user.update_self",
            {
                "username": "   ",
            },
        )
        self.assert_status_code(response, 400)
        model = self.get_model("user/1")
        assert model.get("username") == "username_srtgb123"
        assert "This username is forbidden." in response.json["message"]

    def test_update_self_strip_space(self) -> None:
        response = self.request(
            "user.update_self",
            {
                "username": " username test ",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "username": "username test",
            },
        )

    def test_update_broken_email(self) -> None:
        self.update_model(
            "user/1",
            {"username": "username_srtgb123"},
        )
        response = self.request(
            "user.update_self",
            {
                "email": "broken@@",
            },
        )
        self.assert_status_code(response, 400)
        assert "email must be valid email." in response.json["message"]
