from tests.system.action.base import BaseActionTestCase


class MotionResetStateActionTest(BaseActionTestCase):
    def test_reset_state_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_workflow/1",
            {
                "meeting_id": 222,
                "name": "test1",
                "state_ids": [76, 77],
                "first_state_id": 76,
            },
        )
        self.create_model(
            "motion_state/76",
            {
                "meeting_id": 222,
                "name": "test0",
                "motion_ids": [],
                "workflow_id": 1,
                "first_state_of_workflow_id": 1,
            },
        )
        self.create_model(
            "motion_state/77",
            {"meeting_id": 222, "name": "test1", "motion_ids": [22], "workflow_id": 1},
        )
        self.create_model(
            "motion/22", {"meeting_id": 222, "title": "test1", "state_id": 77}
        )
        response = self.client.post(
            "/", json=[{"action": "motion.reset_state", "data": [{"id": 22}]}]
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76

    def test_reset_state_missing_first_state(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_workflow/1",
            {"meeting_id": 222, "name": "test1", "state_ids": [76, 77]},
        )
        self.create_model(
            "motion_state/76",
            {"meeting_id": 222, "name": "test0", "motion_ids": [], "workflow_id": 1},
        )
        self.create_model(
            "motion_state/77",
            {"meeting_id": 222, "name": "test1", "motion_ids": [22], "workflow_id": 1},
        )
        self.create_model(
            "motion/22", {"meeting_id": 222, "title": "test1", "state_id": 77}
        )
        response = self.client.post(
            "/", json=[{"action": "motion.reset_state", "data": [{"id": 22}]}]
        )
        self.assert_status_code(response, 400)
        self.assertIn(" has no first_state_id.", str(response.data))
