from openslides_backend.models.models import AgendaItem
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class AgendaItemActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "topic/102": {"agenda_item_id": 1, "meeting_id": 1},
                "agenda_item/111": {
                    "item_number": "101",
                    "duration": 600,
                    "meeting_id": 1,
                    "content_object_id": "topic/1",
                },
            }
        )

    def test_update_all_fields(self) -> None:
        self.set_models(
            {
                "tag/1": {"meeting_id": 1},
            }
        )
        response = self.request(
            "agenda_item.update",
            {
                "id": 111,
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
        model = self.get_model("agenda_item/111")
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
                "agenda_item/111": {
                    "child_ids": [222],
                },
                "agenda_item/222": {
                    "type": AgendaItem.AGENDA_ITEM,
                    "item_number": "102",
                    "parent_id": 111,
                    "meeting_id": 1,
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

    def test_update_tag_ids_add(self) -> None:
        self.set_models(
            {
                "tag/1": {"name": "tag", "meeting_id": 1},
            }
        )
        response = self.request("agenda_item.update", {"id": 111, "tag_ids": [1]})
        self.assert_status_code(response, 200)
        agenda_item = self.get_model("agenda_item/111")
        self.assertEqual(agenda_item.get("tag_ids"), [1])

    def test_update_tag_ids_remove(self) -> None:
        self.test_update_tag_ids_add()
        response = self.request("agenda_item.update", {"id": 111, "tag_ids": []})
        self.assert_status_code(response, 200)
        agenda_item = self.get_model("agenda_item/111")
        self.assertEqual(agenda_item.get("tag_ids"), [])

    def test_update_multiple_with_tag(self) -> None:
        self.set_models(
            {
                "tag/1": {
                    "name": "tag",
                    "meeting_id": 1,
                    "tagged_ids": ["agenda_item/1", "agenda_item/2"],
                },
                "agenda_item/1": {"comment": "test", "meeting_id": 1, "tag_ids": [1]},
                "agenda_item/2": {"comment": "test", "meeting_id": 1, "tag_ids": [1]},
            }
        )
        response = self.request_multi(
            "agenda_item.update", [{"id": 1, "tag_ids": []}, {"id": 2, "tag_ids": []}]
        )
        self.assert_status_code(response, 200)
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("tag_ids"), [])
        agenda_item = self.get_model("agenda_item/2")
        self.assertEqual(agenda_item.get("tag_ids"), [])
        tag = self.get_model("tag/1")
        self.assertEqual(tag.get("tagged_ids"), [])

    def update_multiple_with_type_variations(
        self, variations: list[dict[str, int | str]]
    ) -> None:
        self.set_models(
            {
                "agenda_item/1": {
                    "comment": "test1",
                    "meeting_id": 1,
                    "type": "internal",
                    "child_ids": [2],
                    "is_internal": True,
                },
                "agenda_item/2": {
                    "comment": "test2",
                    "meeting_id": 1,
                    "type": "internal",
                    "parent_id": 1,
                    "child_ids": [3],
                    "is_internal": True,
                },
                "agenda_item/3": {
                    "comment": "test3",
                    "meeting_id": 1,
                    "type": "internal",
                    "parent_id": 2,
                    "is_internal": True,
                },
            }
        )
        response = self.request_multi("agenda_item.update", variations)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "agenda_item/1",
            {
                "comment": "test1",
                "type": "common",
                "is_internal": False,
                "is_hidden": False,
            },
        )
        self.assert_model_exists(
            "agenda_item/2",
            {
                "comment": "test2",
                "type": "internal",
                "is_internal": True,
                "is_hidden": False,
            },
        )
        self.assert_model_exists(
            "agenda_item/3",
            {
                "comment": "test3",
                "type": "hidden",
                "is_internal": True,
                "is_hidden": True,
            },
        )

    def test_variations_123(self) -> None:
        self.update_multiple_with_type_variations(
            [{"id": 1, "type": "common"}, {"id": 2}, {"id": 3, "type": "hidden"}]
        )

    def test_variations_132(self) -> None:
        self.update_multiple_with_type_variations(
            [{"id": 1, "type": "common"}, {"id": 3, "type": "hidden"}, {"id": 2}]
        )

    def test_variations_213(self) -> None:
        self.update_multiple_with_type_variations(
            [{"id": 2}, {"id": 1, "type": "common"}, {"id": 3, "type": "hidden"}]
        )

    def test_variations_231(self) -> None:
        self.update_multiple_with_type_variations(
            [{"id": 2}, {"id": 3, "type": "hidden"}, {"id": 1, "type": "common"}]
        )

    def test_variations_312(self) -> None:
        self.update_multiple_with_type_variations(
            [{"id": 3, "type": "hidden"}, {"id": 1, "type": "common"}, {"id": 2}]
        )

    def test_variations_321(self) -> None:
        self.update_multiple_with_type_variations(
            [{"id": 3, "type": "hidden"}, {"id": 2}, {"id": 1, "type": "common"}]
        )

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "agenda_item.update",
            {"id": 111, "duration": 1200},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {},
            "agenda_item.update",
            {"id": 111, "duration": 1200},
            Permissions.AgendaItem.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "agenda_item.update",
            {"id": 111, "duration": 1200},
        )

    def test_update_moderator_notes_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "agenda_item.update",
            {"id": 111, "moderator_notes": "test"},
            Permissions.AgendaItem.CAN_MANAGE,
            fail=True,
        )

    def test_update_moderator_notes_permissions(self) -> None:
        self.base_permission_test(
            {},
            "agenda_item.update",
            {"id": 111, "moderator_notes": "test"},
            Permissions.AgendaItem.CAN_MANAGE_MODERATOR_NOTES,
        )
