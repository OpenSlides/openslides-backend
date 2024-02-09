from typing import Any

from tests.system.action.base import BaseActionTestCase


class PersonalNoteCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            "meeting/110": {
                "name": "name_meeting_110",
                "is_active_in_organization_id": 1,
                "meeting_user_ids": [1],
            },
            "meeting_user/1": {
                "meeting_id": 110,
                "user_id": 1,
            },
            "motion/23": {"meeting_id": 110},
            "user/1": {"meeting_ids": [110]},
        }

    def test_create(self) -> None:
        self.set_models(self.test_models)
        response = self.request(
            "personal_note.create", {"content_object_id": "motion/23", "star": True}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("personal_note/1")
        assert model.get("star") is True
        assert model.get("meeting_user_id") == 1
        assert model.get("meeting_id") == 110

    def test_create_empty_data(self) -> None:
        response = self.request("personal_note.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['content_object_id'] properties",
            response.json["message"],
        )

    def test_create_no_star_and_no_html(self) -> None:
        self.set_models(self.test_models)
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
                **self.test_models,
                "personal_note/1": {
                    "star": True,
                    "note": "blablabla",
                    "meeting_user_id": 1,
                    "content_object_id": "motion/23",
                    "meeting_id": 110,
                },
                "meeting_user/1": {"meeting_id": 110, "user_id": 1},
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
            "(meeting_user_id, content_object_id) must be unique.",
            response.json["message"],
        )

    def test_create_no_permission_user_not_in_meeting(self) -> None:
        self.test_models["user/1"]["meeting_ids"] = []
        self.set_models(self.test_models)
        response = self.request(
            "personal_note.create", {"content_object_id": "motion/23", "star": True}
        )
        self.assert_status_code(response, 403)
        assert "User not associated with meeting." in response.json["message"]

    def test_create_no_permission_anon_user(self) -> None:
        self.set_models(self.test_models)
        self.set_anonymous(meeting_id=110)
        response = self.request(
            "personal_note.create",
            {"content_object_id": "motion/23", "star": True},
            anonymous=True,
        )
        self.assert_status_code(response, 403)
        assert (
            "Anonymous is not allowed to execute personal_note.create"
            in response.json["message"]
        )
