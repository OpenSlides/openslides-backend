from tests.system.action.base import BaseActionTestCase


class AssignmentDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("assignment/111", {"title": "title_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "assignment.delete", "data": [{"id": 111}]}],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_deleted("assignment/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("assignment/112", {"title": "title_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "assignment.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("assignment/112")
        self.assertEqual(model.get("title"), "title_srtgb123")
