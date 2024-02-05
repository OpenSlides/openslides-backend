from typing import Any

from tests.system.action.base import BaseActionTestCase


class PersonalNoteUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {"is_active_in_organization_id": 1, "meeting_user_ids": [1]},
            "personal_note/1": {
                "star": True,
                "note": "blablabla",
                "meeting_user_id": 1,
                "meeting_id": 1,
            },
            "user/1": {"meeting_ids": [1], "meeting_user_ids": [1]},
            "meeting_user/1": {
                "user_id": 1,
                "meeting_id": 1,
                "personal_note_ids": [1],
            },
        }

    def test_update_correct(self) -> None:
        # checks permissions too.
        self.set_models(self.test_models)
        response = self.request(
            "personal_note.update", {"id": 1, "star": False, "note": "blopblop"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("personal_note/1")
        assert model.get("star") is False
        assert model.get("note") == "blopblop"

    def test_update_wrong_user(self) -> None:
        self.set_models(self.test_models)
        self.set_models({"personal_note/1": {"meeting_user_id": 2}})
        response = self.request(
            "personal_note.update", {"id": 1, "star": False, "note": "blopblop"}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Cannot change not owned personal note.", response.json["message"]
        )

    def test_update_no_permission_user_not_in_meeting(self) -> None:
        self.test_models["user/1"]["meeting_ids"] = []
        self.set_models(self.test_models)
        response = self.request(
            "personal_note.update", {"id": 1, "star": False, "note": "blopblop"}
        )
        self.assert_status_code(response, 403)
        assert "User not associated with meeting." in response.json["message"]

    def test_create_no_permission_anon_user(self) -> None:
        self.set_models(self.test_models)
        self.set_anonymous()
        response = self.request(
            "personal_note.update",
            {"id": 1, "star": False, "note": "blopblop"},
            anonymous=True,
        )
        self.assert_status_code(response, 403)
        assert (
            "Anonymous is not allowed to execute personal_note.update"
            in response.json["message"]
        )
