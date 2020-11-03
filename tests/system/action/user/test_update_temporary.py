from tests.system.action.base import BaseActionTestCase


class UserUpdateTemporaryActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123", "meeting_id": 222},
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

    def test_update_all_fields(self) -> None:
        self.create_model("meeting/222", {"name": "name_meeting222"})
        self.create_model(
            "user/111",
            {"username": "username_srtgb123", "meeting_id": 222},
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
                            "username": "test_Xcdfgee",
                            "title": "title",
                            "first_name": "first_name",
                            "last_name": "last_name",
                            "is_active": True,
                            "is_physical_person": False,
                            "about_me": "about_me",
                            "gender": "gender",
                            "comment": "comment",
                            "number": "number",
                            "structure_level": "structure_level",
                            "email": "email",
                            "vote_weight": "1.000000",
                            "is_present_in_meeting_ids": [222],
                            "default_password": "password",
                            "group_ids": [7],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("username") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("title") == "title"
        assert model.get("first_name") == "first_name"
        assert model.get("last_name") == "last_name"
        assert model.get("is_active") is True
        assert model.get("is_physical_person") is False
        assert model.get("about_me") == "about_me"
        assert model.get("gender") == "gender"
        assert model.get("comment") == "comment"
        assert model.get("number") == "number"
        assert model.get("structure_level") == "structure_level"
        assert model.get("email") == "email"
        assert model.get("vote_weight") == "1.000000"
        assert model.get("is_present_in_meeting_ids") == [222]
        assert model.get("default_password") == "password"
        assert model.get("group_$222_ids") == [7]
        assert model.get("group_$_ids") == ["222"]
        assert model.get("group_ids") is None

    def test_update_vote_weight(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123", "meeting_id": 222},
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
            "user/111",
            {"username": "username_srtgb123", "meeting_id": 222},
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
            "user/111",
            {"username": "username_srtgb123", "meeting_id": 222},
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
            "user/111",
            {"username": "username_srtgb123", "meeting_id": 222},
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
            "user/111",
            {"username": "username_srtgb123", "meeting_id": 222},
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

    def test_update_invalid_present_meeting(self) -> None:
        self.create_model("meeting/1", {})
        self.create_model("meeting/2", {})
        self.create_model(
            "user/111",
            {"username": "username_srtgb123", "meeting_id": 1},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update_temporary",
                    "data": [{"id": 111, "is_present_in_meeting_ids": [2]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A temporary user can only be present in its respective meeting.",
            str(response.data),
        )
        self.assert_model_exists("user/111", {"is_present_in_meeting_ids": None})

    def test_update_invalid_group(self) -> None:
        self.create_model("meeting/1", {})
        self.create_model("group/2", {"meeting_id": 2})
        self.create_model(
            "user/111",
            {"username": "username_srtgb123", "meeting_id": 1},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "user.update_temporary",
                    "data": [{"id": 111, "group_ids": [2]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The field meeting_id must be equal but differs",
            str(response.data),
        )
        model = self.get_model("user/111")
        assert model.get("group_$222_ids") is None
        assert model.get("group_$_ids") is None
        assert model.get("group_ids") is None
