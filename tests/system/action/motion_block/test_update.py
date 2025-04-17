from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionBlockActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_meeting(11)
        self.set_models(
            {
                "motion_block/111": {"title": "title_srtgb123", "meeting_id": 11},
            }
        )
        response = self.request(
            "motion_block.update", {"id": 111, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_block/111")
        model = self.get_model("motion_block/111")
        assert model.get("title") == "title_Xcdfgee"

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/11": {"is_active_in_organization_id": 1},
                "motion_block/111": {"title": "title_srtgb123", "meeting_id": 11},
            }
        )
        response = self.request(
            "motion_block.update", {"id": 112, "title": "title_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_block/111")
        assert model.get("title") == "title_srtgb123"

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "motion_block/111": {"meeting_id": 1, "title": "title_srtgb123"},
            },
            "motion_block.update",
            {"id": 111, "title": "title_Xcdfgee"},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {
                "motion_block/111": {"meeting_id": 1, "title": "title_srtgb123"},
            },
            "motion_block.update",
            {"id": 111, "title": "title_Xcdfgee"},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "motion_block/111": {"meeting_id": 1, "title": "title_srtgb123"},
            },
            "motion_block.update",
            {"id": 111, "title": "title_Xcdfgee"},
        )
