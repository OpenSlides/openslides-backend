from tests.system.action.base import BaseActionTestCase


class PersonalNoteDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model(
            "personal_note/1", {"star": True, "note": "blablabla", "user_id": 1}
        )
        response = self.client.post(
            "/",
            json=[{"action": "personal_note.delete", "data": [{"id": 1}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("personal_note/1")

    def test_delete_wrong_user_id(self) -> None:
        self.create_model(
            "personal_note/1", {"star": True, "note": "blablabla", "user_id": 2}
        )
        response = self.client.post(
            "/",
            json=[{"action": "personal_note.delete", "data": [{"id": 1}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn("Cannot delete not owned personal note.", str(response.data))
