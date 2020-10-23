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
        model = self.get_model("user/1")
        assert model.get("username") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222

    def test_create_all_fields(self) -> None:
        self.create_model("meeting/222", {"name": "name_shjeuazu"})
        self.create_model("group/1", {"meeting_id": 222})
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
                            "is_committee": True,
                            "about_me": "about_me",
                            "gender": "gender",
                            "comment": "comment",
                            "number": "number",
                            "structure_level": "structure_level",
                            "email": "email",
                            "vote_weight": "1.000000",
                            "is_present_in_meeting_ids": [222],
                            "default_password": "password",
                            "group_ids": [1],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert model.get("username") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("title") == "title"
        assert model.get("first_name") == "first_name"
        assert model.get("last_name") == "last_name"
        assert model.get("is_active") is True
        assert model.get("is_committee") is True
        assert model.get("about_me") == "about_me"
        assert model.get("gender") == "gender"
        assert model.get("comment") == "comment"
        assert model.get("number") == "number"
        assert model.get("structure_level") == "structure_level"
        assert model.get("email") == "email"
        assert model.get("vote_weight") == "1.000000"
        assert model.get("is_present_in_meeting_ids") == [222]
        assert model.get("default_password") == "password"
        assert model.get("group_$222_ids") == [1]
        assert model.get("group_$_ids") == ["222"]
        assert model.get("group_ids") is None

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
        self.assert_model_not_exists("user/1")

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
            "The field meeting_id must be equal but differs", str(response.data),
        )
        self.assert_model_not_exists("user/1")

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "user.create_temporary", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'meeting_id\\', \\'username\\'] properties",
            str(response.data),
        )
        self.assert_model_not_exists("user/1")

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
            "data[0] must not contain {\\'wrong_field\\'} properties",
            str(response.data),
        )
        self.assert_model_not_exists("user/1")
