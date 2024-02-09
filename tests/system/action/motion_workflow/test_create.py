from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionWorkflowSystemTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(
            "meeting/42",
            {"name": "test_name_fsdksjdfhdsfssdf", "is_active_in_organization_id": 1},
        )
        response = self.request(
            "motion_workflow.create", {"name": "test_Xcdfgee", "meeting_id": 42}
        )
        self.assert_status_code(response, 200)
        workflow = self.get_model("motion_workflow/1")
        assert workflow.get("name") == "test_Xcdfgee"
        assert workflow.get("first_state_id") == 1
        assert workflow.get("sequential_number") == 1
        state = self.get_model("motion_state/1")
        assert state.get("workflow_id") == 1
        assert state.get("first_state_of_workflow_id") == 1

    def test_create_empty_data(self) -> None:
        response = self.request("motion_workflow.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'name'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "motion_workflow.create", {"wrong_field": "text_AefohteiF8"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'name'] properties",
            response.json["message"],
        )

    def test_create_simple_workflow(self) -> None:
        self.create_model(
            "meeting/42", {"name": "test_meeting1", "is_active_in_organization_id": 1}
        )
        response = self.request(
            "motion_workflow.create_simple_workflow",
            {"name": "test_Xcdfgee", "meeting_id": 42},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_workflow/1", {"name": "test_Xcdfgee", "first_state_id": 1}
        )
        self.assert_model_exists(
            "motion_state/1",
            {"name": "submitted", "weight": 1, "next_state_ids": [2, 3, 4]},
        )
        self.assert_model_exists(
            "motion_state/2",
            {
                "name": "accepted",
                "weight": 2,
                "previous_state_ids": [1],
                "meeting_id": 42,
                "workflow_id": 1,
            },
        )
        self.assert_model_exists(
            "motion_state/3",
            {"name": "rejected", "weight": 3, "previous_state_ids": [1]},
        )
        self.assert_model_exists(
            "motion_state/4",
            {"name": "not decided", "weight": 4, "previous_state_ids": [1]},
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
