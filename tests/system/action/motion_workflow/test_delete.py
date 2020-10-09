from tests.system.action.base import BaseActionTestCase


class MotionWorkflowSystemTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model(
            "meeting/90",
            {
                "name": "name_testtest",
                "motions_default_workflow_id": 12,
                "motions_default_statute_amendment_workflow_id": 13,
                "motion_workflow_ids": [111, 2],
            },
        )
        self.create_model(
            "motion_workflow/111", {"name": "name_srtgb123", "meeting_id": 90}
        )
        self.create_model("motion_workflow/2", {"meeting_id": 90})
        response = self.client.post(
            "/", json=[{"action": "motion_workflow.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_workflow/111")

    def test_delete_with_states(self) -> None:
        self.create_model(
            "meeting/1", {"motion_workflow_ids": [2, 100]},
        )
        self.create_model("motion_workflow/2", {"meeting_id": 1, "state_ids": [3]})
        self.create_model("motion_state/3", {"workflow_id": 2})
        # needed because you can't delete the last workflow of a meeting
        self.create_model("motion_workflow/100", {"meeting_id": 1})
        response = self.client.post(
            "/", json=[{"action": "motion_workflow.delete", "data": [{"id": 2}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_workflow/2")
        self.assert_model_deleted("motion_state/3")

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion_workflow/112", {"name": "name_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "motion_workflow.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_workflow/112")

    def test_delete_fail_case_default_1(self) -> None:
        self.create_model(
            "meeting/90",
            {
                "name": "name_testtest",
                "motions_default_workflow_id": 111,
                "motions_default_statute_amendment_workflow_id": 13,
                "motion_workflow_ids": [111],
            },
        )
        self.create_model(
            "motion_workflow/111", {"name": "name_srtgb123", "meeting_id": 90}
        )
        response = self.client.post(
            "/", json=[{"action": "motion_workflow.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_workflow/111")
        self.assertIn("Cannot delete a default workflow.", str(response.data))

    def test_delete_fail_case_default_2(self) -> None:
        self.create_model(
            "meeting/90",
            {
                "name": "name_testtest",
                "motions_default_workflow_id": 12,
                "motions_default_statute_amendment_workflow_id": 111,
                "motion_workflow_ids": [111],
            },
        )
        self.create_model(
            "motion_workflow/111", {"name": "name_srtgb123", "meeting_id": 90}
        )
        response = self.client.post(
            "/", json=[{"action": "motion_workflow.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_workflow/111")
        self.assertIn("Cannot delete a default workflow.", str(response.data))

    def test_delete_fail_case_default_3(self) -> None:
        self.create_model(
            "meeting/90",
            {
                "name": "name_testtest",
                "motions_default_workflow_id": 12,
                "motions_default_statute_amendment_workflow_id": 13,
                "motions_default_amendment_workflow_id": 111,
                "motion_workflow_ids": [111],
            },
        )
        self.create_model(
            "motion_workflow/111", {"name": "name_srtgb123", "meeting_id": 90}
        )
        response = self.client.post(
            "/", json=[{"action": "motion_workflow.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_workflow/111")
        self.assertIn("Cannot delete a default workflow.", str(response.data))

    def test_delete_last_workflow(self) -> None:
        self.create_model(
            "meeting/1", {"motion_workflow_ids": [1]},
        )
        self.create_model("motion_workflow/1", {"meeting_id": 1})
        response = self.client.post(
            "/", json=[{"action": "motion_workflow.delete", "data": [{"id": 1}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_workflow/1")
