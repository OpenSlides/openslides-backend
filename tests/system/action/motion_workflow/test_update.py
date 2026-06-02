from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionWorkflowSystemTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_update_correct(self) -> None:
        response = self.request(
            "motion_workflow.update", {"id": 1, "name": "name_Xcdfgee"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_workflow/1", {"name": "name_Xcdfgee"})

    def test_update_wrong_id(self) -> None:
        response = self.request(
            "motion_workflow.update", {"id": 2, "name": "name_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_workflow/1", {"name": "flo"})
        self.assertEqual(
            "Model 'motion_workflow/2' does not exist.", response.json["message"]
        )

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {}, "motion_workflow.update", {"id": 1, "name": "name_Xcdfgee"}
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_workflow.update",
            {"id": 1, "name": "name_Xcdfgee"},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_workflow.update", {"id": 1, "name": "name_Xcdfgee"}
        )
