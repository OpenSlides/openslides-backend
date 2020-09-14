from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MotionStatuteParagraphActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_statute_paragraph.create",
                    "data": [{"title": "test_Xcdfgee"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("motion_statute_paragraph/1"))
        model = self.datastore.get(get_fqid("motion_statute_paragraph/1"))
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("weight") == 0

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "motion_statute_paragraph.create", "data": [{}]}],
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
                    "action": "motion_statute_paragraph.create",
                    "data": [{"wrong_field": "text_AefohteiF8"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'title\\'] properties", str(response.data),
        )
