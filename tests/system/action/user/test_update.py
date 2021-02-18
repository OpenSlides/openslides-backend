from tests.system.action.base import BaseActionTestCase


class UserUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
        )
        response = self.request(
            "user.update", {"id": 111, "username": "username_Xcdfgee"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("username") == "username_Xcdfgee"

    def test_update_some_more_fields(self) -> None:
        self.set_models(
            {
                "user/111": {"username": "username_srtgb123"},
                "meeting/110": {"name": "name_DsJFXoot"},
                "committee/78": {"name": "name_xXRGTLAJ"},
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "username_Xcdfgee",
                "default_vote_weight": "1.700000",
                "organisation_management_level": "can_manage_users",
                "guest_meeting_ids": [110],
                "committee_as_member_ids": [78],
                "committee_as_manager_ids": [78],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("username") == "username_Xcdfgee"
        assert model.get("default_vote_weight") == "1.700000"
        assert model.get("guest_meeting_ids") == [110]
        assert model.get("committee_as_member_ids") == [78]
        assert model.get("committee_as_manager_ids") == [78]
        assert model.get("organisation_management_level") == "can_manage_users"

    def test_update_template_fields(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "meeting/2": {},
                "user/222": {},
                "user/223": {},
                "group/11": {"meeting_id": 1},
                "group/22": {"meeting_id": 2},
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 223,
                "group_$_ids": {1: [11], 2: [22]},
                "vote_delegations_$_from_ids": {42: [222]},
                "comment_$": {1: "comment<iframe></iframe>"},
                "number_$": {2: "number"},
                "structure_level_$": {1: "level_1", 2: "level_2"},
                "about_me_$": {1: "<p>about</p><iframe></iframe>"},
                "vote_weight_$": {1: "1.000000", 2: "2.333333"},
            },
        )
        self.assert_status_code(response, 200)
        user = self.get_model("user/223")
        assert user.get("group_$1_ids") == [11]
        assert user.get("group_$2_ids") == [22]
        assert set(user.get("group_$_ids", [])) == {"1", "2"}
        assert user.get("vote_delegations_$42_from_ids") == [222]
        assert user.get("vote_delegations_$_from_ids") == ["42"]
        assert user.get("comment_$1") == "comment&lt;iframe&gt;&lt;/iframe&gt;"
        assert user.get("comment_$") == ["1"]
        assert user.get("number_$2") == "number"
        assert user.get("number_$") == ["2"]
        assert user.get("structure_level_$1") == "level_1"
        assert user.get("structure_level_$2") == "level_2"
        assert set(user.get("structure_level_$", [])) == {"1", "2"}
        assert user.get("about_me_$1") == "<p>about</p>&lt;iframe&gt;&lt;/iframe&gt;"
        assert user.get("about_me_$") == ["1"]
        assert user.get("vote_weight_$1") == "1.000000"
        assert user.get("vote_weight_$2") == "2.333333"
        assert set(user.get("vote_weight_$", [])) == {"1", "2"}
        user = self.get_model("user/222")
        assert user.get("vote_delegated_$42_to_id") == 223
        assert user.get("vote_delegated_$_to_id") == ["42"]
        group1 = self.get_model("group/11")
        assert group1.get("user_ids") == [223]
        group2 = self.get_model("group/22")
        assert group2.get("user_ids") == [223]
        meeting = self.get_model("meeting/1")
        assert meeting.get("user_ids") == [223]
        meeting = self.get_model("meeting/2")
        assert meeting.get("user_ids") == [223]

    def test_update_wrong_id(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
        )
        response = self.request(
            "user.update", {"id": 112, "username": "username_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("user/111")
        assert model.get("username") == "username_srtgb123"
