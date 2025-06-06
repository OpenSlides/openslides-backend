from typing import Any

from tests.system.action.base import BaseActionTestCase


class PersonalNoteDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            "meeting/111": {
                "personal_note_ids": [1],
                "is_active_in_organization_id": 1,
                "meeting_user_ids": [1],
            },
            "user/1": {
                "meeting_user_ids": [1],
                "meeting_ids": [111],
            },
            "personal_note/1": {
                "star": True,
                "note": "blablabla",
                "meeting_user_id": 1,
                "meeting_id": 111,
            },
            "meeting_user/1": {
                "user_id": 1,
                "meeting_id": 111,
                "personal_note_ids": [1],
            },
        }

    def test_delete_correct(self) -> None:
        # checks permissions too.
        self.set_models(self.test_models)
        response = self.request("personal_note.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("personal_note/1")
        self.assert_model_exists("meeting_user/1", {"personal_note_ids": []})

    def test_delete_wrong_user_id(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "personal_note_ids": [1],
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [2],
                },
                "user/2": {
                    "meeting_user_ids": [2],
                },
                "personal_note/1": {
                    "star": True,
                    "note": "blablabla",
                    "meeting_user_id": 2,
                    "meeting_id": 111,
                },
                "user/1": {"meeting_ids": [111]},
                "meeting_user/2": {
                    "personal_note_ids": [1],
                    "user_id": 2,
                    "meeting_id": 111,
                },
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
            "Anonymous is not allowed to execute personal_note.delete"
            in response.json["message"]
        )
