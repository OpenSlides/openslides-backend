from tests.system.action.base import BaseActionTestCase


class MotionWorkflowSystemTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model("motion_workflow/111", {"name": "name_srtgb123"})
        response = self.request(
            "motion_workflow.update", {"id": 111, "name": "name_Xcdfgee"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_workflow/111")
        model = self.get_model("motion_workflow/111")
        assert model.get("name") == "name_Xcdfgee"

    def test_update_wrong_id(self) -> None:
        self.create_model("motion_workflow/111", {"name": "name_srtgb123"})
        response = self.request(
            "motion_workflow.update", {"id": 112, "name": "name_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_workflow/111")
        assert model.get("name") == "name_srtgb123"
