from tests.system.action.base import BaseActionTestCase


class PersonalNoteDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/111": {"personal_note_ids": [1]},
                "user/1": {
                    "personal_note_$111_ids": [1],
                    "personal_note_$_ids": ["111"],
                    "meeting_ids": [111],
                },
                "personal_note/1": {
                    "star": True,
                    "note": "blablabla",
                    "user_id": 1,
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("personal_note.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("personal_note/1")
        user = self.get_model("user/1")
        assert user.get("personal_note_$111_ids") == []
        assert user.get("personal_note_$_ids") == []

    def test_delete_wrong_user_id(self) -> None:
        self.set_models(
            {
                "meeting/111": {"personal_note_ids": [1]},
                "user/2": {
                    "personal_note_$111_ids": [1],
                    "personal_note_$_ids": ["111"],
                },
                "personal_note/1": {
                    "star": True,
                    "note": "blablabla",
                    "user_id": 2,
                    "meeting_id": 111,
                },
                "user/1": {"meeting_ids": [111]},
            }
        )
        response = self.request("personal_note.delete", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot delete not owned personal note.", response.json["message"]
        )
        self.assert_model_exists("personal_note/1")
