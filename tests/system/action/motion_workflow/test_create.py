from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionWorkflowSystemTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_meeting(42)
        response = self.request(
            "motion_workflow.create", {"name": "test_Xcdfgee", "meeting_id": 42}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_workflow/43",
            {"name": "test_Xcdfgee", "first_state_id": 43, "sequential_number": 2},
        )
        self.assert_model_exists(
            "motion_state/43", {"workflow_id": 43, "first_state_of_workflow_id": 43}
        )

    def test_create_empty_data(self) -> None:
        response = self.request("motion_workflow.create", {})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action motion_workflow.create: data must contain ['meeting_id', 'name'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "motion_workflow.create", {"wrong_field": "text_AefohteiF8"}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action motion_workflow.create: data must contain ['meeting_id', 'name'] properties",
            response.json["message"],
        )

    def test_create_simple_workflow(self) -> None:
        self.create_meeting(42)
        response = self.request(
            "motion_workflow.create_simple_workflow",
            {"name": "test_Xcdfgee", "meeting_id": 42},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_workflow/43",
            {"name": "test_Xcdfgee", "first_state_id": 43, "sequential_number": 2},
        )
        self.assert_model_exists(
            "motion_state/43",
            {"name": "submitted", "weight": 1, "next_state_ids": [44, 45, 46]},
        )
        self.assert_model_exists(
            "motion_state/44",
            {
                "name": "accepted",
                "weight": 2,
                "previous_state_ids": [43],
                "meeting_id": 42,
                "workflow_id": 43,
            },
        )
        self.assert_model_exists(
            "motion_state/45",
            {"name": "rejected", "weight": 3, "previous_state_ids": [43]},
        )
        self.assert_model_exists(
            "motion_state/46",
            {"name": "not decided", "weight": 4, "previous_state_ids": [43]},
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_workflow.create",
            {"name": "test_Xcdfgee", "meeting_id": 1},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_workflow.create",
            {"name": "test_Xcdfgee", "meeting_id": 1},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "motion_workflow.create",
            {"name": "test_Xcdfgee", "meeting_id": 1},
        )
