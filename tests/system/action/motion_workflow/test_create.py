from tests.system.action.base import BaseActionTestCase


class MotionWorkflowSystemTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("meeting/42", {"name": "test_name_fsdksjdfhdsfssdf"})
        response = self.request(
            "motion_workflow.create", {"name": "test_Xcdfgee", "meeting_id": 42}
        )
        self.assert_status_code(response, 200)
        workflow = self.get_model("motion_workflow/1")
        assert workflow.get("name") == "test_Xcdfgee"
        assert workflow.get("first_state_id") == 1
        state = self.get_model("motion_state/1")
        assert state.get("workflow_id") == 1
        assert state.get("first_state_of_workflow_id") == 1

    def test_create_empty_data(self) -> None:
        response = self.request("motion_workflow.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['name', 'meeting_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "motion_workflow.create", {"wrong_field": "text_AefohteiF8"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['name', 'meeting_id'] properties",
            response.json["message"],
        )

    def test_create_simple_workflow(self) -> None:
        self.create_model("meeting/42", {"name": "test_meeting1"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_workflow.create_simple_workflow",
                    "data": [{"name": "test_Xcdfgee", "meeting_id": 42}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_workflow/1", {
            "name": "test_Xcdfgee",
            "first_state_id": 4 })
        self.assert_model_exists(
            "motion_state/1",
            {
                "name": "accepted",
                "previous_state_ids": [4],
                "meeting_id": 42,
                "workflow_id": 1,
            },
        )
        self.assert_model_exists(
            "motion_state/2", {"name": "rejected", "previous_state_ids": [4]}
        )
        self.assert_model_exists(
            "motion_state/3", {"name": "not_decided", "previous_state_ids": [4]}
        )
        self.assert_model_exists(
            "motion_state/4", {"name": "submitted", "next_state_ids": [1, 2, 3]}
        )
