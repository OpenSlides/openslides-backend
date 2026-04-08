from tests.system.action.base import BaseActionTestCase


class PersonalNoteDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(111)
        self.set_user_groups(1, [111])
        self.set_models(
            {
                "personal_note/1": {
                    "star": True,
                    "note": "blablabla",
                    "meeting_user_id": 1,
                    "meeting_id": 111,
                },
            }
        )

    def test_delete_correct(self) -> None:
        response = self.request("personal_note.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("personal_note/1")
        self.assert_model_exists("meeting_user/1", {"personal_note_ids": None})

    def test_delete_wrong_user_id(self) -> None:
        self.create_user_for_meeting(111)
        self.login(2)
        response = self.request("personal_note.delete", {"id": 1})
        self.assert_status_code(response, 403)
        self.assertEqual(
            "Cannot delete not owned personal note.", response.json["message"]
        )
        self.assert_model_exists("personal_note/1")

    def test_delete_no_permission_anon_user(self) -> None:
        self.set_anonymous(meeting_id=111)
        response = self.request("personal_note.delete", {"id": 1}, anonymous=True)
        self.assert_status_code(response, 403)
        self.assertEqual(
            "Anonymous is not allowed to execute personal_note.delete",
            response.json["message"],
        )
