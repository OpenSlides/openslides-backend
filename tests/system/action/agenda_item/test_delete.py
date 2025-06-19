from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class AgendaItemActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(20)

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "agenda_item/111": {"meeting_id": 20},
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("agenda_item/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "agenda_item/112": {"meeting_id": 20},
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("agenda_item/112")

    def test_delete_topic(self) -> None:
        self.set_models(
            {
                "topic/34": {"agenda_item_id": 111, "meeting_id": 20},
                "agenda_item/111": {"content_object_id": "topic/34", "meeting_id": 20},
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("agenda_item/111")
        self.assert_model_deleted("topic/34")

    def test_delete_with_motion(self) -> None:
        self.set_models(
            {
                "motion/34": {"agenda_item_id": 111, "meeting_id": 20},
                "agenda_item/111": {"content_object_id": "motion/34", "meeting_id": 20},
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("agenda_item/111")
        self.assert_model_exists("motion/34")

    def test_delete_with_projection(self) -> None:
        self.set_models(
            {
                "meeting/20": {
                    "all_projection_ids": [1],
                },
                "motion/34": {"agenda_item_id": 111, "meeting_id": 20},
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
                    "meeting_id": 20,
                },
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("agenda_item/111")
        self.assert_model_exists("motion/34")
        self.assert_model_deleted("projection/1")
        self.assert_model_exists("projector/1", {"current_projection_ids": []})

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "motion/34": {"agenda_item_id": 111, "meeting_id": 1},
                "agenda_item/111": {"content_object_id": "motion/34", "meeting_id": 1},
            },
            "agenda_item.delete",
            {"id": 111},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {
                "motion/34": {"agenda_item_id": 111, "meeting_id": 1},
                "agenda_item/111": {"content_object_id": "motion/34", "meeting_id": 1},
            },
            "agenda_item.delete",
            {"id": 111},
            Permissions.AgendaItem.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "motion/34": {"agenda_item_id": 111, "meeting_id": 1},
                "agenda_item/111": {"content_object_id": "motion/34", "meeting_id": 1},
            },
            "agenda_item.delete",
            {"id": 111},
        )
