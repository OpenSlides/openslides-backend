from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class AgendaItemActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(20)

    def test_delete_correct(self) -> None:
        self.create_meeting(20)
        self.set_models(
            {
                "agenda_item/111": {"meeting_id": 20, "content_object_id": "topic/1"},
                "topic/1": {
                    "meeting_id": 20,
                    "title": "tropic",
                    "sequential_number": 1,
                },
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("agenda_item/111")

    def test_delete_wrong_id(self) -> None:
        self.create_meeting(20)
        self.set_models(
            {
                "agenda_item/112": {"meeting_id": 20, "content_object_id": "topic/1"},
                "topic/1": {
                    "meeting_id": 20,
                    "title": "tropic",
                    "sequential_number": 1,
                },
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("agenda_item/112")

    def test_delete_topic(self) -> None:
        self.create_meeting(20)
        self.set_models(
            {
                "topic/34": {
                    "title": "tropic",
                    "sequential_number": 1,
                    "agenda_item_id": 111,
                    "meeting_id": 20,
                },
                "agenda_item/111": {"content_object_id": "topic/34", "meeting_id": 20},
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("agenda_item/111")
        self.assert_model_not_exists("topic/34")

    def test_delete_with_motion(self) -> None:
        self.create_meeting(20)
        self.create_motion(20, 34)
        self.set_models(
            {"agenda_item/111": {"content_object_id": "motion/34", "meeting_id": 20}}
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("agenda_item/111")
        self.assert_model_exists("motion/34")

    def test_delete_with_projection(self) -> None:
        self.create_meeting(20)
        self.create_motion(20, 34)
        self.set_models(
            {
                "meeting/20": {
                    "all_projection_ids": [1],
                },
                "agenda_item/111": {
                    "content_object_id": "motion/34",
                    "projection_ids": [1],
                    "meeting_id": 20,
                },
                "projection/1": {
                    "content_object_id": "agenda_item/111",
                    "current_projector_id": 1,
                    "meeting_id": 20,
                },
                "projector/1": {
                    "current_projection_ids": [1],
                    "sequential_number": 1,
                    "meeting_id": 20,
                },
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("agenda_item/111")
        self.assert_model_exists("motion/34")
        self.assert_model_not_exists("projection/1")
        self.assert_model_exists("projector/1", {"current_projection_ids": None})

    def test_delete_no_permissions(self) -> None:
        self.create_meeting(1)
        self.create_motion(1, 34)
        self.base_permission_test(
            {
                "agenda_item/111": {"content_object_id": "motion/34", "meeting_id": 1},
            },
            "agenda_item.delete",
            {"id": 111},
        )

    def test_delete_permissions(self) -> None:
        self.create_meeting(1)
        self.create_motion(1, 34)
        self.base_permission_test(
            {
                "agenda_item/111": {"content_object_id": "motion/34", "meeting_id": 1},
            },
            "agenda_item.delete",
            {"id": 111},
            Permissions.AgendaItem.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.create_meeting(1)
        self.create_motion(1, 34)
        self.base_locked_out_superadmin_permission_test(
            {
                "agenda_item/111": {"content_object_id": "motion/34", "meeting_id": 1},
            },
            "agenda_item.delete",
            {"id": 111},
        )
