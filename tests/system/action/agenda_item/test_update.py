from openslides_backend.models.models import AgendaItem
from tests.system.action.base import BaseActionTestCase


class AgendaItemActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model("topic/102", {"name": "topic_kHemtGYY"})
        self.create_model(
            "agenda_item/111",
            {"item_number": 101, "duration": 600},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.update",
                    "data": [{"id": 111, "duration": 1200}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("agenda_item/111")
        assert model.get("duration") == 1200

    def test_update_all_fields(self) -> None:
        self.create_model("meeting/1", {"name": "test"})
        self.create_model("topic/1", {"agenda_item_id": 1, "meeting_id": 1})
        self.create_model("tag/1", {"meeting_id": 1})
        self.create_model(
            "agenda_item/1", {"meeting_id": 1, "content_object_id": "topic/1"}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.update",
                    "data": [
                        {
                            "id": 1,
                            "duration": 1200,
                            "item_number": "12",
                            "comment": "comment",
                            "closed": True,
                            "type": AgendaItem.HIDDEN_ITEM,
                            "weight": 333,
                            "tag_ids": [1],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("agenda_item/1")
        assert model.get("duration") == 1200
        assert model.get("item_number") == "12"
        assert model.get("comment") == "comment"
        assert model.get("closed") is True
        assert model.get("type") == AgendaItem.HIDDEN_ITEM
        assert model.get("weight") == 333
        assert model.get("tag_ids") == [1]

    def test_update_type_change_with_children(self) -> None:
        self.create_model(
            "agenda_item/111",
            {"item_number": 101, "duration": 600, "child_ids": [222]},
        )
        self.create_model(
            "agenda_item/222",
            {"type": AgendaItem.AGENDA_ITEM, "item_number": 102, "parent_id": 111},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.update",
                    "data": [{"id": 111, "type": AgendaItem.HIDDEN_ITEM}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("agenda_item/111")
        assert model.get("type") == AgendaItem.HIDDEN_ITEM
        assert model.get("is_hidden") is True
        assert model.get("is_internal") is False
        child_model = self.get_model("agenda_item/222")
        assert child_model.get("type") == AgendaItem.AGENDA_ITEM
        assert child_model.get("is_hidden") is True
        assert child_model.get("is_internal") is False
