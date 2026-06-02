from tests.system.action.base import BaseActionTestCase


class PersonalNoteCreateActionTest(BaseActionTestCase):
    def set_test_models(self) -> None:
        self.create_meeting()
        self.set_user_groups(1, [1])
        self.create_motion(1, 23)

    def test_create(self) -> None:
        self.set_test_models()
        response = self.request(
            "personal_note.create", {"content_object_id": "motion/23", "star": True}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "personal_note/1",
            {
                "star": True,
                "content_object_id": "motion/23",
                "meeting_user_id": 1,
                "meeting_id": 1,
            },
        )

    def test_create_empty_data(self) -> None:
        response = self.request("personal_note.create", {})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action personal_note.create: data must contain ['content_object_id'] properties",
            response.json["message"],
        )

    def test_create_no_star_and_no_html(self) -> None:
        self.set_test_models()
        response = self.request(
            "personal_note.create", {"content_object_id": "motion/23"}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Can't create personal note without star or note.", response.json["message"]
        )

    def test_create_not_unique(self) -> None:
        self.set_test_models()
        self.set_models(
            {
                "personal_note/1": {
                    "star": True,
                    "note": "blablabla",
                    "meeting_user_id": 1,
                    "content_object_id": "motion/23",
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "personal_note.create",
            {"note": "blablabla", "content_object_id": "motion/23"},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "(meeting_user_id, content_object_id) must be unique.",
            response.json["message"],
        )

    def test_create_no_permission_user_not_in_meeting(self) -> None:
        self.create_meeting()
        self.create_motion(1, 23)
        response = self.request(
            "personal_note.create", {"content_object_id": "motion/23", "star": True}
        )
        self.assert_status_code(response, 403)
        self.assertEqual("User not associated with meeting.", response.json["message"])

    def test_create_no_permission_anon_user(self) -> None:
        self.set_test_models()
        self.set_anonymous(meeting_id=1)
        response = self.request(
            "personal_note.create",
            {"content_object_id": "motion/23", "star": True},
            anonymous=True,
        )
        self.assert_status_code(response, 403)
        self.assertEqual(
            "Anonymous is not allowed to execute personal_note.create",
            response.json["message"],
        )

    def test_create_other_meeting_user_error(self) -> None:
        self.set_test_models()
        response = self.request(
            "personal_note.create",
            {"meeting_user_id": 2, "content_object_id": "motion/23", "star": True},
            internal=False,
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "data must not contain {'meeting_user_id'} properties",
            response.json["message"],
        )

    def test_create_other_meeting_user(self) -> None:
        self.set_test_models()
        self.create_user("dummy", [1])
        response = self.request(
            "personal_note.create",
            {"meeting_user_id": 2, "content_object_id": "motion/23", "star": True},
            internal=True,
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "personal_note/1",
            {
                "star": True,
                "content_object_id": "motion/23",
                "meeting_user_id": 2,
                "meeting_id": 1,
            },
        )

    def test_create_not_in_meeting(self) -> None:
        self.create_meeting()
        self.create_motion(1, 23)
        response = self.request(
            "personal_note.create", {"content_object_id": "motion/23", "star": True}
        )
        self.assert_status_code(response, 403)
        assert "User not associated with meeting." in response.json["message"]
