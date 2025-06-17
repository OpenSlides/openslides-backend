from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionWorkflowSystemTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/90": {
                    "name": "name_testtest",
                    "motions_default_workflow_id": 12,
                    "motion_workflow_ids": [111, 2],
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "motion_workflow/111": {"name": "name_srtgb123", "meeting_id": 90},
                "motion_workflow/2": {"meeting_id": 90},
            }
        )
        response = self.request("motion_workflow.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_workflow/111")

    def test_delete_with_states(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "motion_workflow_ids": [2, 100],
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "motion_workflow/2": {"meeting_id": 1, "state_ids": [3]},
                "motion_state/3": {"workflow_id": 2, "meeting_id": 1},
                "motion_workflow/100": {"meeting_id": 1},
            }
        )
        response = self.request("motion_workflow.delete", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_workflow/2")
        self.assert_model_deleted("motion_state/3")

    def test_delete_with_first_state(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "motion_workflow_ids": [2, 100],
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "motion_workflow/2": {
                    "meeting_id": 1,
                    "state_ids": [3],
                    "first_state_id": 3,
                },
                "motion_state/3": {
                    "workflow_id": 2,
                    "first_state_of_workflow_id": 2,
                    "meeting_id": 1,
                },
                "motion_workflow/100": {"meeting_id": 1},
            }
        )
        response = self.request("motion_workflow.delete", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_workflow/2")
        self.assert_model_deleted("motion_state/3")

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion_workflow/112", {"name": "name_srtgb123"})
        response = self.request("motion_workflow.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_workflow/112")

    def test_delete_fail_case_default_1(self) -> None:
        self.set_models(
            {
                "meeting/90": {
                    "name": "name_testtest",
                    "motions_default_workflow_id": 111,
                    "motion_workflow_ids": [111],
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "motion_workflow/111": {"name": "name_srtgb123", "meeting_id": 90},
            }
        )
        response = self.request("motion_workflow.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_workflow/111")
        self.assertIn(
            "You cannot delete the workflow as long as it is selected as default workflow for new motions in the settings.",
            response.json["message"],
        )

    def test_delete_fail_case_default_2(self) -> None:
        self.set_models(
            {
                "meeting/90": {
                    "name": "name_testtest",
                    "motions_default_workflow_id": 12,
                    "motion_workflow_ids": [111],
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "motion_workflow/111": {"name": "name_srtgb123", "meeting_id": 90},
            }
        )
        response = self.request("motion_workflow.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_workflow/111")
        self.assertIn(
            "You cannot delete the last workflow of a meeting.",
            response.json["message"],
        )

    def test_delete_fail_case_default_3(self) -> None:
        self.set_models(
            {
                "meeting/90": {
                    "name": "name_testtest",
                    "motions_default_workflow_id": 12,
                    "motions_default_amendment_workflow_id": 111,
                    "motion_workflow_ids": [111],
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "motion_workflow/111": {"name": "name_srtgb123", "meeting_id": 90},
            }
        )
        response = self.request("motion_workflow.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_workflow/111")
        self.assertIn(
            "You cannot delete the workflow as long as it is selected as default workflow for new amendments in the settings.",
            response.json["message"],
        )

    def test_delete_last_workflow(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "motion_workflow_ids": [1],
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "motion_workflow/1": {"meeting_id": 1},
            }
        )
        response = self.request("motion_workflow.delete", {"id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_workflow/1")

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "meeting/1": {
                    "name": "name_testtest",
                    "motions_default_workflow_id": 12,
                    "motion_workflow_ids": [111, 2],
                    "is_active_in_organization_id": 1,
                },
                "motion_workflow/111": {"name": "name_srtgb123", "meeting_id": 1},
                "motion_workflow/2": {"meeting_id": 1},
            },
            "motion_workflow.delete",
            {"id": 111},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {
                "meeting/1": {
                    "name": "name_testtest",
                    "motions_default_workflow_id": 12,
                    "motion_workflow_ids": [111, 2],
                    "is_active_in_organization_id": 1,
                },
                "motion_workflow/111": {"name": "name_srtgb123", "meeting_id": 1},
                "motion_workflow/2": {"meeting_id": 1},
            },
            "motion_workflow.delete",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "meeting/1": {
                    "name": "name_testtest",
                    "motions_default_workflow_id": 12,
                    "motion_workflow_ids": [111, 2],
                    "is_active_in_organization_id": 1,
                },
                "motion_workflow/111": {"name": "name_srtgb123", "meeting_id": 1},
                "motion_workflow/2": {"meeting_id": 1},
            },
            "motion_workflow.delete",
            {"id": 111},
        )
