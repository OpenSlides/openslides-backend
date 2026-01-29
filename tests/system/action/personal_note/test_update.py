from tests.system.action.base import BaseActionTestCase


class PersonalNoteUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(1)
        self.set_user_groups(1, [1])
        self.set_models(
            {
                "personal_note/1": {
                    "star": True,
                    "note": "blablabla",
                    "meeting_user_id": 1,
                    "meeting_id": 1,
                },
            }
        )

    def test_update_correct(self) -> None:
        response = self.request(
            "personal_note.update", {"id": 1, "star": False, "note": "blopblop"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("personal_note/1", {"star": False, "note": "blopblop"})

    def test_update_wrong_user(self) -> None:
        self.create_user_for_meeting(1)
        self.login(2)
        response = self.request(
            "personal_note.update", {"id": 1, "star": False, "note": "blopblop"}
        )
        self.assert_status_code(response, 403)
        self.assertEqual(
            "Cannot change not owned personal note.", response.json["message"]
        )
        self.assert_model_exists("personal_note/1", {"star": True, "note": "blablabla"})

    def test_create_no_permission_anon_user(self) -> None:
        self.set_anonymous(meeting_id=1)
        response = self.request(
            "personal_note.update",
            {"id": 1, "star": False, "note": "blopblop"},
            anonymous=True,
        )
        self.assert_status_code(response, 403)
        self.assertEqual(
            "Anonymous is not allowed to execute personal_note.update",
            response.json["message"],
        )
