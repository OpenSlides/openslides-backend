from tests.system.action.base import BaseActionTestCase


class UserUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
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
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("username") == "username_Xcdfgee"

    def test_update_some_more_fields(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
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
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("username") == "username_Xcdfgee"
        assert model.get("vote_weight") == "1.700000"
        assert model.get("guest_meeting_ids") == [110]
        assert model.get("committee_as_member_ids") == [78]
        assert model.get("committee_as_manager_ids") == [78]

    def test_update_group_ids(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
        )
        self.create_model(
            "group/11",
            {"meeting_id": 1},
        )
        self.create_model(
            "group/22",
            {"meeting_id": 2},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update",
                    "data": [{"id": 111, "group_ids": [11, 22]}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("group_$1_ids") == [11]
        assert user.get("group_$2_ids") == [22]
        assert set(user.get("group_$_ids", [])) == {"1", "2"}
        group1 = self.get_model("group/11")
        assert group1.get("user_ids") == [111]
        group2 = self.get_model("group/22")
        assert group2.get("user_ids") == [111]

    def test_update_vote_delegations(self) -> None:
        self.create_model(
            "user/111",
            {},
        )
        self.create_model(
            "user/222",
            {},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update",
                    "data": [{"id": 111, "vote_delegations_from_ids": {42: [222]}}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        assert user.get("vote_delegations_$42_from_ids") == [222]
        assert user.get("vote_delegations_$_from_ids") == ["42"]
        user = self.get_model("user/222")
        assert user.get("vote_delegated_$42_to_id") == 111
        assert user.get("vote_delegated_$_to_id") == ["42"]

    def test_update_wrong_id(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
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
