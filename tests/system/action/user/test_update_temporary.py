from tests.system.action.base import BaseActionTestCase


class UserUpdateTemporaryActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(
            "user/111", {"username": "username_srtgb123"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update_temporary",
                    "data": [{"id": 111, "username": "username_Xcdfgee"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model = self.get_model("user/111")
        assert model.get("username") == "username_Xcdfgee"

    def test_update_wrong_id(self) -> None:
        self.create_model(
            "user/111", {"username": "username_srtgb123"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update_temporary",
                    "data": [{"id": 112, "username": "username_Xcdfgee"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("user/111")
        assert model.get("username") == "username_srtgb123"
