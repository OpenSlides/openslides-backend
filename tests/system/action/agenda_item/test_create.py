from tests.system.action.base import BaseActionTestCase


class AgendaItemSystemTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("meeting/2", {"name": "test"})
        self.create_model("topic/1", {"name": "test", "meeting_id": 2})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.create",
                    "data": [{"content_object_id": "topic/1"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("agenda_item/1")
        self.assertFalse(model.get("meta_deleted"))
        self.assertEqual(model.get("meeting_id"), 2)
        self.assertEqual(model.get("content_object_id"), "topic/1")

        model = self.get_model("meeting/2")
        self.assertEqual(model.get("agenda_item_ids"), [1])

        model = self.get_model("topic/1")
        self.assertEqual(model.get("agenda_item_id"), 1)

    def test_create_more_fields(self) -> None:
        self.create_model("meeting/1", {"name": "test"})
        self.create_model("topic/1", {"name": "test", "meeting_id": 1})
        self.create_model("agenda_item/42", {"comment": "test"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.create",
                    "data": [
                        {
                            "content_object_id": "topic/1",
                            "comment": "test_comment_oiuoitesfd",
                            "type": 2,
                            "parent_id": 42,
                            "duration": 360,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        agenda_item = self.get_model("agenda_item/43")
        self.assertEqual(agenda_item["comment"], "test_comment_oiuoitesfd")
        self.assertEqual(agenda_item["type"], 2)
        self.assertEqual(agenda_item["parent_id"], 42)
        self.assertEqual(agenda_item["duration"], 360)
        self.assertEqual(agenda_item["weight"], 0)
        self.assertFalse(agenda_item.get("closed"))

    def test_create_content_object_does_not_exist(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.create",
                    "data": [{"content_object_id": "topic/1"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("agenda_item/1")

    def test_create_meeting_does_not_exist(self) -> None:
        self.create_model("topic/1", {"name": "test", "meeting_id": 2})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.create",
                    "data": [{"content_object_id": "topic/1"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("agenda_item/1")
