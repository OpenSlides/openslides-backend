from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MotionBlockActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {"action": "motion_block.create", "data": [{"title": "test_Xcdfgee"}]}
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("motion_block/1"))
        model = self.datastore.get(get_fqid("motion_block/1"))
        assert model.get("title") == "test_Xcdfgee"

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "motion_block.create", "data": [{}]}],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'title\\'] properties", str(response.data),
        )

    def test_create_wrong_field(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_block.create",
                    "data": [{"wrong_field": "text_AefohteiF8"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'title\\'] properties", str(response.data),
        )
