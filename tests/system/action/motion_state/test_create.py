from tests.system.action.base import BaseActionTestCase


class MotionStateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("motion_workflow/42", {"name": "test_name_fjwnq8d8tje8"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_state.create",
                    "data": [{"name": "test_Xcdfgee", "workflow_id": 42}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/1")
        model = self.get_model("motion_state/1")
        assert model.get("name") == "test_Xcdfgee"

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "motion_state.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'name\\', \\'workflow_id\\'] properties",
            str(response.data),
        )

    def test_create_wrong_field(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_state.create",
                    "data": [{"wrong_field": "text_AefohteiF8"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'name\\', \\'workflow_id\\'] properties",
            str(response.data),
        )
