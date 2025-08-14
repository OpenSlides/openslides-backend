from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionBlockActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "motion_block/111": {
                    "title": "title_srtgb123",
                    "sequential_number": 111,
                    "list_of_speakers_id": 222,
                    "meeting_id": 1,
                },
                "list_of_speakers/222": {
                    "closed": False,
                    "sequential_number": 15,
                    "content_object_id": "motion_block/111",
                    "meeting_id": 1,
                },
            }
        )

    def test_delete_correct(self) -> None:
        response = self.request("motion_block.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_block/111")

    def test_delete_wrong_id(self) -> None:
        response = self.request("motion_block.delete", {"id": 112})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Model 'motion_block/112' does not exist.", response.json["message"]
        )
        self.assert_model_exists("motion_block/111")

    def test_delete_correct_cascading(self) -> None:
        self.set_models(
            {
                "motion_block/111": {"agenda_item_id": 333},
                "agenda_item/333": {
                    "comment": "test_comment_ewoirzewoirioewr",
                    "content_object_id": "motion_block/111",
                    "meeting_id": 1,
                },
                "projection/1": {
                    "content_object_id": "motion_block/111",
                    "current_projector_id": 1,
                    "meeting_id": 1,
                },
                "projector/1": {"sequential_number": 1, "meeting_id": 1},
            }
        )
        response = self.request("motion_block.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_block/111")
        self.assert_model_not_exists("agenda_item/333")
        self.assert_model_not_exists("list_of_speakers/222")
        self.assert_model_not_exists("projection/1")
        self.assert_model_exists("projector/1", {"current_projection_ids": None})

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test({}, "motion_block.delete", {"id": 111})

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_block.delete",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_block.delete", {"id": 111}
        )
