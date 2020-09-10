from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MotionStateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(
            get_fqid("motion_workflow/42"), {"name": "test_name_fjwnq8d8tje8"}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_state.create",
                    "data": [{"name": "test_Xcdfgee", "workflow_id": 42}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("motion_state/1"))
        model = self.datastore.get(get_fqid("motion_state/1"))
        assert model.get("name") == "test_Xcdfgee"

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "motion_state.create", "data": [{}]}],
        )
        self.assertEqual(response.status_code, 400)
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
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'name\\', \\'workflow_id\\'] properties",
            str(response.data),
        )
