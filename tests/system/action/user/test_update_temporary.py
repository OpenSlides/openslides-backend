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

    def test_update_some_fields(self) -> None:
        self.create_model("meeting/222", {"name": "name_meeting222"})
        self.create_model(
            "user/111", {"username": "username_srtgb123"},
        )
        self.create_model(
            "group/7", {"name": "name_group7", "user_ids": [], "meeting_id": 222}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update_temporary",
                    "data": [
                        {
                            "id": 111,
                            "vote_weight": "1.500000",
                            "default_password": "1q2w3e4r5t6z",
                            "group__ids": [7],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("vote_weight") == "1.500000"
        assert model.get("default_password") == "1q2w3e4r5t6z"
        assert model.get("group__ids") == [7]

    def test_update_vote_weight(self) -> None:
        self.create_model(
            "user/111", {"username": "username_srtgb123"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update_temporary",
                    "data": [{"id": 111, "vote_weight": "1.500000"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model = self.get_model("user/111")
        assert model.get("vote_weight") == "1.500000"

    def test_update_vote_weight_two_digits(self) -> None:
        self.create_model(
            "user/111", {"username": "username_srtgb123"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update_temporary",
                    "data": [{"id": 111, "vote_weight": "10.500000"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model = self.get_model("user/111")
        assert model.get("vote_weight") == "10.500000"

    def test_update_vote_weight_invalid_number(self) -> None:
        self.create_model(
            "user/111", {"username": "username_srtgb123"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update_temporary",
                    "data": [{"id": 111, "vote_weight": 1.5}],
                }
            ],
        )
        self.assertEqual(response.status_code, 400)
        model = self.get_model("user/111")
        assert model.get("vote_weight") is None

    def test_update_vote_weight_invalid_string(self) -> None:
        self.create_model(
            "user/111", {"username": "username_srtgb123"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update_temporary",
                    "data": [{"id": 111, "vote_weight": "a.aaaaaa"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 400)
        model = self.get_model("user/111")
        assert model.get("vote_weight") is None

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
