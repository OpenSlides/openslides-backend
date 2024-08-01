from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionBlockActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/11": {"is_active_in_organization_id": 1},
                "motion_block/111": {"meeting_id": 11},
            }
        )
        response = self.request("motion_block.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_block/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/11": {"is_active_in_organization_id": 1},
                "motion_block/112": {"meeting_id": 11},
            }
        )
        response = self.request("motion_block.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_block/112")

    def test_delete_correct_cascading(self) -> None:
        self.set_models(
            {
                "meeting/12": {
                    "is_active_in_organization_id": 1,
                    "all_projection_ids": [1],
                },
                "motion_block/111": {
                    "list_of_speakers_id": 222,
                    "agenda_item_id": 333,
                    "projection_ids": [1],
                    "meeting_id": 12,
                },
                "list_of_speakers/222": {
                    "closed": False,
                    "content_object_id": "motion_block/111",
                    "meeting_id": 12,
                },
                "agenda_item/333": {
                    "comment": "test_comment_ewoirzewoirioewr",
                    "content_object_id": "motion_block/111",
                    "meeting_id": 12,
                },
                "projection/1": {
                    "content_object_id": "motion_block/111",
                    "current_projector_id": 1,
                    "meeting_id": 12,
                },
                "projector/1": {
                    "current_projection_ids": [1],
                    "meeting_id": 12,
                },
            }
        )
        response = self.request("motion_block.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_block/111")
        self.assert_model_deleted("agenda_item/333")
        self.assert_model_deleted("list_of_speakers/222")
        self.assert_model_deleted("projection/1")
        self.assert_model_exists("projector/1", {"current_projection_ids": []})

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            {"motion_block/111": {"meeting_id": 1}},
            "motion_block.delete",
            {"id": 111},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {"motion_block/111": {"meeting_id": 1}},
            "motion_block.delete",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {"motion_block/111": {"meeting_id": 1}},
            "motion_block.delete",
            {"id": 111},
        )
