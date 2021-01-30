from tests.system.action.base import BaseActionTestCase


class UserCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        response = self.client.post(
            "/",
            json=[{"action": "user.create", "data": [{"username": "test_Xcdfgee"}]}],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/2")
        assert model.get("username") == "test_Xcdfgee"

    def test_create_some_more_fields(self) -> None:
        self.create_model("meeting/110", {"name": "name_DsJFXoot"})
        self.create_model("meeting/111", {"name": "name_xXRGTLAJ"})
        self.create_model("committee/78", {"name": "name_TSXpBGdt"})
        self.create_model("committee/79", {"name": "name_hOldWvVF"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.create",
                    "data": [
                        {
                            "username": "test_Xcdfgee",
                            "default_vote_weight": "1.500000",
                            "organisation_management_level": "can_manage_users",
                            "guest_meeting_ids": [110, 111],
                            "committee_as_member_ids": [78],
                            "committee_as_manager_ids": [79],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/2")
        assert model.get("username") == "test_Xcdfgee"
        assert model.get("default_vote_weight") == "1.500000"
        assert model.get("guest_meeting_ids") == [110, 111]
        assert model.get("committee_as_member_ids") == [78]
        assert model.get("committee_as_manager_ids") == [79]
        assert model.get("organisation_management_level") == "can_manage_users"
        # check meeting.user_ids
        meeting = self.get_model("meeting/110")
        assert meeting.get("user_ids") == [2]
        meeting = self.get_model("meeting/111")
        assert meeting.get("user_ids") == [2]

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/",
            json=[{"action": "user.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain [\\'username\\'] properties",
            str(response.data),
        )

    def test_create_wrong_field(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.create",
                    "data": [{"wrong_field": "text_AefohteiF8", "username": "test1"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {\\'wrong_field\\'} properties",
            str(response.data),
        )
