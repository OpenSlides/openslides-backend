from openslides_backend.models.models import AgendaItem
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class AgendaItemNumberingTester(BaseActionTestCase):
    """
    Tests agenda item numbering action.
    """

    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_numbering(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "agenda_item_ids": [1, 2, 3],
                    "is_active_in_organization_id": 1,
                },
                "agenda_item/1": {
                    "meeting_id": 1,
                    "weight": 10,
                    "type": AgendaItem.AGENDA_ITEM,
                },
                "agenda_item/2": {
                    "meeting_id": 1,
                    "weight": 10,
                    "parent_id": 1,
                    "type": AgendaItem.AGENDA_ITEM,
                },
                "agenda_item/3": {
                    "meeting_id": 1,
                    "parent_id": 1,
                    "weight": 11,
                    "type": AgendaItem.AGENDA_ITEM,
                },
            }
        )
        response = self.request("agenda_item.numbering", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        agenda_item_1 = self.get_model("agenda_item/1")
        assert agenda_item_1.get("item_number") == "1"
        agenda_item_2 = self.get_model("agenda_item/2")
        assert agenda_item_2.get("item_number") == "1.1"
        agenda_item_3 = self.get_model("agenda_item/3")
        assert agenda_item_3.get("item_number") == "1.2"

    def test_numbering_prefix(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "agenda_item_ids": [1, 2, 3],
                    "agenda_number_prefix": "P-",
                    "is_active_in_organization_id": 1,
                },
                "agenda_item/1": {
                    "meeting_id": 1,
                    "weight": 10,
                    "type": AgendaItem.AGENDA_ITEM,
                },
                "agenda_item/2": {
                    "meeting_id": 1,
                    "weight": 11,
                    "parent_id": 1,
                    "type": AgendaItem.AGENDA_ITEM,
                },
                "agenda_item/3": {
                    "meeting_id": 1,
                    "parent_id": 1,
                    "weight": 12,
                    "type": AgendaItem.AGENDA_ITEM,
                },
            }
        )
        response = self.request("agenda_item.numbering", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        agenda_item_1 = self.get_model("agenda_item/1")
        assert agenda_item_1.get("item_number") == "P- 1"
        agenda_item_2 = self.get_model("agenda_item/2")
        assert agenda_item_2.get("item_number") == "P- 1.1"
        agenda_item_3 = self.get_model("agenda_item/3")
        assert agenda_item_3.get("item_number") == "P- 1.2"

    def test_numbering_roman(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "agenda_item_ids": [1, 2, 3],
                    "agenda_numeral_system": "roman",
                    "is_active_in_organization_id": 1,
                },
                "agenda_item/1": {
                    "meeting_id": 1,
                    "weight": 10,
                    "type": AgendaItem.AGENDA_ITEM,
                },
                "agenda_item/2": {
                    "meeting_id": 1,
                    "weight": 11,
                    "parent_id": 1,
                    "type": AgendaItem.AGENDA_ITEM,
                },
                "agenda_item/3": {
                    "meeting_id": 1,
                    "parent_id": 1,
                    "weight": 12,
                    "type": AgendaItem.AGENDA_ITEM,
                },
            }
        )
        response = self.request("agenda_item.numbering", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        agenda_item_1 = self.get_model("agenda_item/1")
        assert agenda_item_1.get("item_number") == "I"
        agenda_item_2 = self.get_model("agenda_item/2")
        assert agenda_item_2.get("item_number") == "I.1"
        agenda_item_3 = self.get_model("agenda_item/3")
        assert agenda_item_3.get("item_number") == "I.2"

    def test_numbering_without_parents(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "agenda_item_ids": [1, 2],
                    "is_active_in_organization_id": 1,
                },
                "agenda_item/1": {
                    "meeting_id": 1,
                    "weight": 10,
                    "type": AgendaItem.AGENDA_ITEM,
                },
                "agenda_item/2": {
                    "meeting_id": 1,
                    "weight": 11,
                    "type": AgendaItem.AGENDA_ITEM,
                },
            }
        )
        response = self.request("agenda_item.numbering", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        agenda_item_1 = self.get_model("agenda_item/1")
        assert agenda_item_1.get("item_number") == "1"
        agenda_item_2 = self.get_model("agenda_item/2")
        assert agenda_item_2.get("item_number") == "2"

    def test_numbering_with_non_public_items(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "agenda_item_ids": [1, 2],
                    "is_active_in_organization_id": 1,
                },
                "agenda_item/1": {
                    "meeting_id": 1,
                    "weight": 10,
                    "type": AgendaItem.AGENDA_ITEM,
                },
                "agenda_item/2": {
                    "meeting_id": 1,
                    "weight": 10,
                    "type": AgendaItem.INTERNAL_ITEM,
                },
            }
        )
        response = self.request("agenda_item.numbering", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        agenda_item_1 = self.get_model("agenda_item/1")
        assert agenda_item_1.get("item_number") == "1"
        agenda_item_2 = self.get_model("agenda_item/2")
        assert agenda_item_2.get("item_number") == ""

    def test_numbering_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "meeting/1": {
                    "agenda_item_ids": [1, 2],
                    "is_active_in_organization_id": 1,
                },
                "agenda_item/1": {
                    "meeting_id": 1,
                    "weight": 10,
                    "type": AgendaItem.AGENDA_ITEM,
                },
                "agenda_item/2": {
                    "meeting_id": 1,
                    "weight": 10,
                    "type": AgendaItem.AGENDA_ITEM,
                },
            },
            "agenda_item.numbering",
            {"meeting_id": 1},
        )

    def test_numbering_permissions(self) -> None:
        self.base_permission_test(
            {
                "meeting/1": {
                    "agenda_item_ids": [1, 2],
                    "is_active_in_organization_id": 1,
                },
                "agenda_item/1": {
                    "meeting_id": 1,
                    "weight": 10,
                    "type": AgendaItem.AGENDA_ITEM,
                },
                "agenda_item/2": {
                    "meeting_id": 1,
                    "weight": 10,
                    "type": AgendaItem.AGENDA_ITEM,
                },
            },
            "agenda_item.numbering",
            {"meeting_id": 1},
            Permissions.AgendaItem.CAN_MANAGE,
        )

    def test_numbering_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "meeting/1": {
                    "agenda_item_ids": [1, 2],
                    "is_active_in_organization_id": 1,
                },
                "agenda_item/1": {
                    "meeting_id": 1,
                    "weight": 10,
                    "type": AgendaItem.AGENDA_ITEM,
                },
                "agenda_item/2": {
                    "meeting_id": 1,
                    "weight": 10,
                    "type": AgendaItem.AGENDA_ITEM,
                },
            },
            "agenda_item.numbering",
            {"meeting_id": 1},
        )
