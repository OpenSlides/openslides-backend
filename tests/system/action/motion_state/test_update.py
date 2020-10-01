from tests.system.action.base import BaseActionTestCase


class MotionStateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(
            "motion_workflow/110", {"name": "name_Ycefgee", "state_ids": [111]},
        )
        self.create_model(
            "motion_state/111", {"name": "name_srtgb123", "workflow_id": 110}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_state.update",
                    "data": [{"id": 111, "name": "name_Xcdfgee"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/111")
        model = self.get_model("motion_state/111")
        assert model.get("name") == "name_Xcdfgee"

    def test_update_correct_plus_next_previous(self) -> None:
        self.create_model(
            "motion_workflow/110",
            {"name": "name_Ycefgee", "state_ids": [111, 112, 113]},
        )
        self.create_model(
            "motion_state/111", {"name": "name_srtgb123", "workflow_id": 110}
        )
        self.create_model(
            "motion_state/112", {"name": "name_srtfg112", "workflow_id": 110}
        )
        self.create_model(
            "motion_state/113", {"name": "name_srtfg113", "workflow_id": 110}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_state.update",
                    "data": [
                        {
                            "id": 111,
                            "next_state_ids": [112],
                            "previous_state_ids": [113],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_state/111")
        assert model.get("next_state_ids") == [112]
        assert model.get("previous_state_ids") == [113]

    def test_update_wrong_workflow_mismatch(self) -> None:
        self.create_model(
            "motion_workflow/110", {"name": "name_Ycefgee", "state_ids": [111, 112]},
        )
        self.create_model(
            "motion_workflow/90", {"name": "name_Ycefgee", "state_ids": [113]},
        )
        self.create_model(
            "motion_state/111", {"name": "name_srtgb123", "workflow_id": 110}
        )
        self.create_model(
            "motion_state/112", {"name": "name_srtfg112", "workflow_id": 110}
        )
        self.create_model(
            "motion_state/113", {"name": "name_srtfg113", "workflow_id": 90}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_state.update",
                    "data": [
                        {
                            "id": 111,
                            "next_state_ids": [112],
                            "previous_state_ids": [113],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Cannot update: found states from different workflows" in str(
            response.data
        )

    def test_update_wrong_id(self) -> None:
        self.create_model("motion_state/111", {"name": "name_srtgb123"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_state.update",
                    "data": [{"id": 112, "name": "name_Xcdfgee"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_state/111")
        assert model.get("name") == "name_srtgb123"
