from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MotionBlockActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(get_fqid("meeting/42"), {"name": "test"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_block.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 42,
                            "agenda_create": True,
                        }
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("motion_block/1"))
        model = self.datastore.get(get_fqid("motion_block/1"))
        self.assertEqual(model.get("title"), "test_Xcdfgee")
        self.assertEqual(
            self.datastore.get(get_fqid(f"agenda_item/{model['agenda_item_id']}")),
            {
                "type": 1,
                "weight": 0,
                "meeting_id": 42,
                "content_object_id": "motion_block/1",
                "meta_deleted": False,
                "meta_position": 2,
            },
        )

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "motion_block.create", "data": [{}]}],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'title\\', \\'meeting_id\\'] properties",
            str(response.data),
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
            "data[0] must contain [\\'title\\', \\'meeting_id\\'] properties",
            str(response.data),
        )
