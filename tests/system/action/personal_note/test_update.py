from tests.system.action.base import BaseActionTestCase


class PersonalNoteUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "personal_note/1": {
                    "star": True,
                    "note": "blablabla",
                    "user_id": 1,
                    "meeting_id": 1,
                },
                "user/1": {"meeting_ids": [1]},
            }
        )
        response = self.request(
            "personal_note.update", {"id": 1, "star": False, "note": "blopblop"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("personal_note/1")
        assert model.get("star") is False
        assert model.get("note") == "blopblop"

    def test_update_wrong_user(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "personal_note/1": {"star": True, "note": "blablabla", "user_id": 2},
                "user/1": {"meeting_ids": [1]},
            }
        )
        response = self.request(
            "personal_note.update", {"id": 1, "star": False, "note": "blopblop"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot change not owned personal note.", response.json["message"]
        )
