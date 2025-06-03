from openslides_backend.models.models import AgendaItem
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionBlockActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(
            "meeting/42",
            {
                "name": "test",
                "agenda_item_creation": "always",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
        )
        response = self.request(
            "motion_block.create", {"title": "test_Xcdfgee", "meeting_id": 42}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_block/1")
        self.assertEqual(model.get("title"), "test_Xcdfgee")
        self.assertEqual(model.get("sequential_number"), 1)
        self.assert_model_exists(
            f"agenda_item/{model['agenda_item_id']}",
            {
                "id": 1,
                "is_hidden": False,
                "is_internal": False,
                "level": 0,
                "type": AgendaItem.AGENDA_ITEM,
                "weight": 1,
                "meeting_id": 42,
                "content_object_id": "motion_block/1",
                "meta_deleted": False,
            },
        )
        self.assert_model_exists(
            "list_of_speakers/1", {"content_object_id": "motion_block/1"}
        )

    def test_create_empty_data(self) -> None:
        response = self.request("motion_block.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'title'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "motion_block.create", {"wrong_field": "text_AefohteiF8"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'title'] properties",
            response.json["message"],
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "meeting/1": {
                    "name": "test",
                    "agenda_item_creation": "always",
                    "is_active_in_organization_id": 1,
                }
            },
            "motion_block.create",
            {"title": "test_Xcdfgee", "meeting_id": 1},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {
                "meeting/1": {
                    "name": "test",
                    "agenda_item_creation": "always",
                    "is_active_in_organization_id": 1,
                }
            },
            "motion_block.create",
            {"title": "test_Xcdfgee", "meeting_id": 1},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "meeting/1": {
                    "name": "test",
                    "agenda_item_creation": "always",
                    "is_active_in_organization_id": 1,
                }
            },
            "motion_block.create",
            {"title": "test_Xcdfgee", "meeting_id": 1},
        )
