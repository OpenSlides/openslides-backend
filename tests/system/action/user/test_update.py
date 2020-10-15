from tests.system.action.base import BaseActionTestCase


class UserUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(
            "user/111", {"username": "username_srtgb123"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update",
                    "data": [{"id": 111, "username": "username_Xcdfgee"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model = self.get_model("user/111")
        assert model.get("username") == "username_Xcdfgee"

    def test_update_some_more_fields(self) -> None:
        self.create_model(
            "user/111", {"username": "username_srtgb123"},
        )
        self.create_model("meeting/110", {"name": "name_DsJFXoot"})
        self.create_model("committee/78", {"name": "name_xXRGTLAJ"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update",
                    "data": [
                        {
                            "id": 111,
                            "username": "username_Xcdfgee",
                            "vote_weight": "1.700000",
                            "guest_meeting_ids": [110],
                            "committee_as_member_ids": [78],
                            "committee_as_manager_ids": [78],
                        }
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        model = self.get_model("user/111")
        assert model.get("username") == "username_Xcdfgee"
        assert model.get("vote_weight") == "1.700000"
        assert model.get("guest_meeting_ids") == [110]
        assert model.get("committee_as_member_ids") == [78]
        assert model.get("committee_as_manager_ids") == [78]

    def test_update_wrong_id(self) -> None:
        self.create_model(
            "user/111", {"username": "username_srtgb123"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update",
                    "data": [{"id": 112, "username": "username_Xcdfgee"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("user/111")
        assert model.get("username") == "username_srtgb123"
