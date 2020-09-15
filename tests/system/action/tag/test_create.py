from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class TagActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(get_fqid("meeting/577"), {"name": "name_YBEqrXqz"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "tag.create",
                    "data": [{"name": "test_Xcdfgee", "meeting_id": 577}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("tag/1"))
        model = self.datastore.get(get_fqid("tag/1"))
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("meeting_id") == 577

    def test_create_empty_data(self) -> None:
        response = self.client.post("/", json=[{"action": "tag.create", "data": [{}]}])
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'name\\', \\'meeting_id\\'] properties",
            str(response.data),
        )

    def test_create_wrong_field(self) -> None:
        self.create_model(get_fqid("meeting/577"), {"name": "name_YBEqrXqz"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "tag.create",
                    "data": [
                        {
                            "name": "test_Xcdfgee",
                            "meeting_id": 577,
                            "wrong_field": "text_AefohteiF8",
                        }
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain only specified properties", str(response.data),
        )
