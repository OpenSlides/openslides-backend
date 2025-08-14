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

    def test_update_correct(self) -> None:
        response = self.request(
            "motion_block.update", {"id": 111, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_block/111", {"title": "title_Xcdfgee"})

    def test_update_wrong_id(self) -> None:
        response = self.request(
            "motion_block.update", {"id": 112, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Model 'motion_block/112' does not exist.", response.json["message"]
        )
        self.assert_model_exists("motion_block/111", {"title": "title_srtgb123"})

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {}, "motion_block.update", {"id": 111, "title": "title_Xcdfgee"}
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_block.update",
            {"id": 111, "title": "title_Xcdfgee"},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_block.update", {"id": 111, "title": "title_Xcdfgee"}
        )
