from tests.system.action.base import BaseActionTestCase


class PersonalNoteUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        # checks permissions too.
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
                "personal_note/1": {
                    "star": True,
                    "note": "blablabla",
                    "user_id": 2,
                    "meeting_id": 1,
                },
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

    def test_update_no_permission_user_not_in_meeting(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "personal_note/1": {
                    "star": True,
                    "note": "blablabla",
                    "user_id": 1,
                    "meeting_id": 1,
                },
                "user/1": {"meeting_ids": []},
            }
        )
        response = self.request(
            "personal_note.update", {"id": 1, "star": False, "note": "blopblop"}
        )
        self.assert_status_code(response, 403)
        assert "User not associated with meeting." in response.json["message"]

    def test_create_no_permission_anon_user(self) -> None:
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
        self.set_anonymous()
        response = self.request(
            "personal_note.update",
            {"id": 1, "star": False, "note": "blopblop"},
            anonymous=True,
        )
        self.assert_status_code(response, 403)
        assert (
            "Anonymous user cannot do personal_note.update." in response.json["message"]
        )
