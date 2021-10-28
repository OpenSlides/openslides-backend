from openslides_backend.models.models import AgendaItem
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class AgendaItemActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/11": {"is_active_in_organization_id": 1},
                "topic/102": {"meeting_id": 11},
                "agenda_item/111": {
                    "item_number": "101",
                    "duration": 600,
                    "meeting_id": 11,
                },
            }
        )
        response = self.request("agenda_item.update", {"id": 111, "duration": 1200})
        self.assert_status_code(response, 200)
        model = self.get_model("agenda_item/111")
        assert model.get("duration") == 1200

    def test_update_all_fields(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "test", "is_active_in_organization_id": 1},
                "topic/1": {"agenda_item_id": 1, "meeting_id": 1},
                "tag/1": {"meeting_id": 1},
                "agenda_item/1": {"meeting_id": 1, "content_object_id": "topic/1"},
            }
        )
        response = self.request(
            "agenda_item.update",
            {
                "id": 1,
                "duration": 1200,
                "item_number": "12",
                "comment": "comment",
                "closed": True,
                "type": AgendaItem.HIDDEN_ITEM,
                "weight": 333,
                "tag_ids": [1],
            },
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
        self.set_models(
            {
                "meeting/11": {"is_active_in_organization_id": 1},
                "agenda_item/111": {
                    "item_number": "101",
                    "duration": 600,
                    "child_ids": [222],
                    "meeting_id": 11,
                },
                "agenda_item/222": {
                    "type": AgendaItem.AGENDA_ITEM,
                    "item_number": "102",
                    "parent_id": 111,
                    "meeting_id": 11,
                },
            }
        )
        response = self.request(
            "agenda_item.update", {"id": 111, "type": AgendaItem.HIDDEN_ITEM}
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

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "topic/102": {"meeting_id": 1},
                "agenda_item/111": {
                    "item_number": "101",
                    "duration": 600,
                    "meeting_id": 1,
                },
            },
            "agenda_item.update",
            {"id": 111, "duration": 1200},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {
                "topic/102": {"meeting_id": 1},
                "agenda_item/111": {
                    "item_number": "101",
                    "duration": 600,
                    "meeting_id": 1,
                },
            },
            "agenda_item.update",
            {"id": 111, "duration": 1200},
            Permissions.AgendaItem.CAN_MANAGE,
        )
