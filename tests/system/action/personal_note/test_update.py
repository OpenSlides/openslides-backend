from tests.system.action.base import BaseActionTestCase


class PersonalNoteUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(
            "personal_note/1", {"star": True, "note": "blablabla", "user_id": 1}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "personal_note.update",
                    "data": [{"id": 1, "star": False, "note": "blopblop"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("personal_note/1")
        assert model.get("star") is False
        assert model.get("note") == "blopblop"

    def test_update_wrong_user(self) -> None:
        self.create_model(
            "personal_note/1", {"star": True, "note": "blablabla", "user_id": 2}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "personal_note.update",
                    "data": [{"id": 1, "star": False, "note": "blopblop"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot change not owned personal note.", response.json.get("message", "")
        )
