from tests.system.action.base import BaseActionTestCase


class PersonalNoteDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("meeting/111", {"personal_note_ids": [1]})
        self.update_model(
            "user/1", {"personal_note_$111_ids": [1], "personal_note_$_ids": ["111"]}
        )
        self.create_model(
            "personal_note/1",
            {"star": True, "note": "blablabla", "user_id": 1, "meeting_id": 111},
        )
        response = self.client.post(
            "/",
            json=[{"action": "personal_note.delete", "data": [{"id": 1}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("personal_note/1")
        user = self.get_model("user/1")
        assert user.get("personal_note_$111_ids") == []
        assert user.get("personal_note_$_ids") == []

    def test_delete_wrong_user_id(self) -> None:
        self.create_model("meeting/111", {"personal_note_ids": [1]})
        self.create_model(
            "user/2", {"personal_note_$111_ids": [1], "personal_note_$_ids": ["111"]}
        )
        self.create_model(
            "personal_note/1",
            {"star": True, "note": "blablabla", "user_id": 2, "meeting_id": 111},
        )
        response = self.client.post(
            "/",
            json=[{"action": "personal_note.delete", "data": [{"id": 1}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn("Cannot delete not owned personal note.", str(response.data))
        self.assert_model_exists("personal_note/1")
