from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionWorkflowSystemTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "motion_workflow/2": {
                    "name": "workflow 2",
                    "meeting_id": 1,
                    "first_state_id": 2,
                },
                "motion_state/2": {
                    "name": "state of workflow 2",
                    "workflow_id": 2,
                    "meeting_id": 1,
                    "weight": 2,
                },
            }
        )

    def test_delete_correct(self) -> None:
        response = self.request("motion_workflow.delete", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_workflow/2")
        self.assert_model_not_exists("motion_state/2")

    def test_delete_wrong_id(self) -> None:
        response = self.request("motion_workflow.delete", {"id": 3})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Model 'motion_workflow/3' does not exist.", response.json["message"]
        )

    def test_delete_fail_default_motion_workflow(self) -> None:
        response = self.request("motion_workflow.delete", {"id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_workflow/1")
        self.assertIn(
            "You cannot delete the workflow as long as it is selected as default workflow for new motions in the settings.",
            response.json["message"],
        )

    def test_delete_fail_default_amendment_workflow(self) -> None:
        self.set_models({"meeting/1": {"motions_default_amendment_workflow_id": 2}})
        response = self.request("motion_workflow.delete", {"id": 2})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_workflow/2")
        self.assertIn(
            "You cannot delete the workflow as long as it is selected as default workflow for new amendments in the settings.",
            response.json["message"],
        )

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test({}, "motion_workflow.delete", {"id": 2})

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {}, "motion_workflow.delete", {"id": 2}, Permissions.Motion.CAN_MANAGE
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_workflow.delete", {"id": 2}
        )
