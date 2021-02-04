from tests.system.action.base import BaseActionTestCase


class UserCreateTemporaryActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("meeting/222", {"name": "name_shjeuazu"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.create_temporary",
                    "data": [{"username": "test_Xcdfgee", "meeting_id": 222}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/2")
        assert model.get("username") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("is_physical_person") is True

    def test_create_all_fields(self) -> None:
        self.create_model("meeting/222", {"name": "name_shjeuazu"})
        self.create_model("group/1", {"meeting_id": 222})
        self.create_model("user/7", {})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.create_temporary",
                    "data": [
                        {
                            "username": "test_Xcdfgee",
                            "meeting_id": 222,
                            "title": "title",
                            "first_name": "first_name",
                            "last_name": "last_name",
                            "is_active": True,
                            "is_physical_person": False,
                            "gender": "gender",
                            "default_number": "number",
                            "default_structure_level": "structure_level",
                            "email": "email",
                            "default_vote_weight": "1.000000",
                            "is_present_in_meeting_ids": [222],
                            "default_password": "password",
                            "group_ids": [1],
                            "vote_delegations_from_ids": [7],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/8")
        assert model.get("username") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("title") == "title"
        assert model.get("first_name") == "first_name"
        assert model.get("last_name") == "last_name"
        assert model.get("is_active") is True
        assert model.get("is_physical_person") is False
        assert model.get("gender") == "gender"
        assert model.get("default_number") == "number"
        assert model.get("default_structure_level") == "structure_level"
        assert model.get("email") == "email"
        assert model.get("default_vote_weight") == "1.000000"
        assert model.get("is_present_in_meeting_ids") == [222]
        assert model.get("default_password") == "password"
        assert model.get("group_$222_ids") == [1]
        assert model.get("group_$_ids") == ["222"]
        assert model.get("group_ids") is None
        assert model.get("vote_delegations_$222_from_ids") == [7]
        assert model.get("vote_delegations_$_from_ids") == ["222"]
        assert model.get("vote_delegations_from_ids") is None
        # check meeting.user_ids
        meeting = self.get_model("meeting/222")
        assert meeting.get("user_ids") == [8]

    def test_create_invalid_present_meeting(self) -> None:
        self.create_model("meeting/1", {})
        self.create_model("meeting/2", {})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.create_temporary",
                    "data": [
                        {
                            "username": "test_Xcdfgee",
                            "meeting_id": 1,
                            "is_present_in_meeting_ids": [2],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A temporary user can only be present in its respective meeting.",
            str(response.data),
        )
        self.assert_model_not_exists("user/2")

    def test_create_invalid_group(self) -> None:
        self.create_model("meeting/1", {})
        self.create_model("group/2", {"meeting_id": 2})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.create_temporary",
                    "data": [
                        {"username": "test_Xcdfgee", "meeting_id": 1, "group_ids": [2]}
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "requires the following fields to be equal",
            str(response.data),
        )
        self.assert_model_not_exists("user/2")

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/",
            json=[{"action": "user.create_temporary", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain [\\'meeting_id\\', \\'username\\'] properties",
            str(response.data),
        )
        self.assert_model_not_exists("user/2")

    def test_create_wrong_field(self) -> None:
        self.create_model("meeting/222", {"name": "name_shjeuazu"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.create_temporary",
                    "data": [
                        {
                            "wrong_field": "text_AefohteiF8",
                            "username": "test1",
                            "meeting_id": 222,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {\\'wrong_field\\'} properties",
            str(response.data),
        )
        self.assert_model_not_exists("user/2")

    def test_create_invalid_vote_delegation(self) -> None:
        self.create_model("meeting/222", {})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.create_temporary",
                    "data": [
                        {
                            "username": "test_Xcdfgee",
                            "meeting_id": 222,
                            "vote_delegations_from_ids": [7],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following users were not found",
            str(response.data),
        )
        self.assert_model_not_exists("user/2")
