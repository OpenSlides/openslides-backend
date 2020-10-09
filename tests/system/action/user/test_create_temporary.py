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

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "user.create_temporary", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'meeting_id\\', \\'username\\'] properties",
            str(response.data),
        )

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
