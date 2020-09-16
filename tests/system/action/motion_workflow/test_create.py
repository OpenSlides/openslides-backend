from tests.system.action.base import BaseActionTestCase


class MotionWorkflowSystemTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("meeting/42", {"name": "test_name_fsdksjdfhdsfssdf"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_workflow.create",
                    "data": [{"name": "test_Xcdfgee", "meeting_id": 42}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_workflow/1")
        model = self.get_model("motion_workflow/1")
        assert model.get("name") == "test_Xcdfgee"

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "motion_workflow.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'name\\', \\'meeting_id\\'] properties",
            str(response.data),
        )

    def test_create_wrong_field(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_workflow.create",
                    "data": [{"wrong_field": "text_AefohteiF8"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'name\\', \\'meeting_id\\'] properties",
            str(response.data),
        )
