from tests.system.action.base import BaseActionTestCase


class UserCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        response = self.client.post(
            "/",
            json=[{"action": "user.create", "data": [{"username": "test_Xcdfgee"}]}],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert model.get("username") == "test_Xcdfgee"

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "user.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'username\\'] properties", str(response.data),
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
            "data[0] must not contain {\\'wrong_field\\'} properties",
            str(response.data),
        )
