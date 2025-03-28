from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionWorkflowSystemTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/10": {"is_active_in_organization_id": 1, "committee_id": 1},
                "motion_workflow/111": {"name": "name_srtgb123", "meeting_id": 10},
            }
        )
        response = self.request(
            "motion_workflow.update", {"id": 111, "name": "name_Xcdfgee"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_workflow/111")
        model = self.get_model("motion_workflow/111")
        assert model.get("name") == "name_Xcdfgee"

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/10": {"is_active_in_organization_id": 1, "committee_id": 1},
                "motion_workflow/111": {"name": "name_srtgb123", "meeting_id": 10},
            }
        )
        response = self.request(
            "motion_workflow.update", {"id": 112, "name": "name_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_workflow/111")
        assert model.get("name") == "name_srtgb123"

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "motion_workflow/111": {"name": "name_srtgb123", "meeting_id": 1},
            },
            "motion_workflow.update",
            {"id": 111, "name": "name_Xcdfgee"},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {
                "motion_workflow/111": {"name": "name_srtgb123", "meeting_id": 1},
            },
            "motion_workflow.update",
            {"id": 111, "name": "name_Xcdfgee"},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "motion_workflow/111": {"name": "name_srtgb123", "meeting_id": 1},
            },
            "motion_workflow.update",
            {"id": 111, "name": "name_Xcdfgee"},
        )
