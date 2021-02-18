from tests.system.action.base import BaseActionTestCase


class PersonalNoteCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.set_models(
            {
                "meeting/110": {"name": "name_meeting_110"},
                "motion/23": {"meeting_id": 110},
            }
        )
        response = self.request(
            "personal_note.create", {"content_object_id": "motion/23", "star": True}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("personal_note/1")
        assert model.get("star") is True
        assert model.get("user_id") == 1
        assert model.get("meeting_id") == 110

    def test_create_empty_data(self) -> None:
        response = self.request("personal_note.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['content_object_id'] properties",
            response.json["message"],
        )

    def test_create_no_star_and_no_html(self) -> None:
        self.set_models(
            {
                "meeting/110": {"name": "name_meeting_110"},
                "motion/23": {"meeting_id": 110},
            }
        )
        response = self.request(
            "personal_note.create", {"content_object_id": "motion/23"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Can't create personal note without star or note.",
            response.json["message"],
        )

    def test_create_not_unique(self) -> None:
        self.set_models(
            {
                "meeting/110": {"name": "name_meeting_110"},
                "motion/23": {"meeting_id": 110},
                "personal_note/1": {
                    "star": True,
                    "note": "blablabla",
                    "user_id": 1,
                    "content_object_id": "motion/23",
                },
            }
        )
        response = self.request(
            "personal_note.create",
            {
                "note": "blablabla",
                "content_object_id": "motion/23",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "(user_id, content_object_id) must be unique.",
            response.json["message"],
        )
