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

    def test_update_self_about_me(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("test", group_ids=[1])
        self.login(self.user_id)
        self.update_model("user/2", {"meeting_ids": [1]})
        response = self.request(
            "user.update_self",
            {
                "about_me_$": {
                    "1": "This is for meeting/1",
                }
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"about_me_$1": "This is for meeting/1"})

    def test_update_self_about_me_wrong_meeting(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("test", group_ids=[1])
        self.login(self.user_id)
        self.set_models(
            {
                "user/2": {"meeting_ids": [1]},
                "meeting/2": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request(
            "user.update_self",
            {
                "about_me_$": {
                    "1": "This is for meeting/1",
                    "2": "This is for meeting/2",
                }
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "User may update about_me_$ only in his meetings, but tries in [2]",
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
