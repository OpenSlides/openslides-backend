from typing import Any, Dict

from tests.system.action.base import BaseActionTestCase


class PersonalNoteDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: Dict[str, Dict[str, Any]] = {
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

    def test_delete_correct(self) -> None:
        # checks permissions too.
        self.set_models(self.test_models)
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
        self.assert_status_code(response, 403)
        self.assertIn(
            "Cannot delete not owned personal note.", response.json["message"]
        )
        self.assert_model_exists("personal_note/1")

    def test_delete_no_permission_user_not_in_meeting(self) -> None:
        self.test_models["user/1"]["meeting_ids"] = []
        self.set_models(self.test_models)
        response = self.request("personal_note.delete", {"id": 1})
        self.assert_status_code(response, 403)
        assert "User not associated with meeting." in response.json["message"]

    def test_delete_no_permission_anon_user(self) -> None:
        self.set_models(self.test_models)
        self.set_anonymous(meeting_id=111)
        response = self.request(
            "personal_note.delete",
            {"id": 1},
            anonymous=True,
        )
        self.assert_status_code(response, 403)
        assert (
            "Anonymous user cannot do personal_note.delete." in response.json["message"]
        )
