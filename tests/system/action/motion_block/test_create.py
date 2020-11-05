from tests.system.action.base import BaseActionTestCase


class MotionBlockActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(
            "meeting/42", {"name": "test", "agenda_item_creation": "always"}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_block.create",
                    "data": [{"title": "test_Xcdfgee", "meeting_id": 42}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_block/1")
        model = self.get_model("motion_block/1")
        self.assertEqual(model.get("title"), "test_Xcdfgee")
        self.assertEqual(
            self.get_model(f"agenda_item/{model['agenda_item_id']}"),
            {
                "id": 1,
                "is_hidden": False,
                "is_internal": False,
                "level": 0,
                "type": 1,
                "weight": 10000,
                "meeting_id": 42,
                "content_object_id": "motion_block/1",
                "meta_deleted": False,
                "meta_position": 2,
            },
        )
        self.assert_model_exists(
            "list_of_speakers/1", {"content_object_id": "motion_block/1"}
        )

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/",
            json=[{"action": "motion_block.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
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
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'title\\', \\'meeting_id\\'] properties",
            str(response.data),
        )
