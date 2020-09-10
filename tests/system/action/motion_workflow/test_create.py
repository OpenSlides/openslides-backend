from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MotionWorkflowSystemTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(
            get_fqid("meeting/42"), {"name": "test_name_fsdksjdfhdsfssdf"}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_workflow.create",
                    "data": [{"name": "test_Xcdfgee", "meeting_id": 42}],
                }
            ],
        )
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("motion_workflow/1"))
        model = self.datastore.get(get_fqid("motion_workflow/1"))
        assert model.get("name") == "test_Xcdfgee"

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "motion_workflow.create", "data": [{}]}],
        )
        self.assertEqual(response.status_code, 400)
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
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'name\\', \\'meeting_id\\'] properties",
            str(response.data),
        )
