from tests.system.action.base import BaseActionTestCase


class MeetingUserCreate(BaseActionTestCase):
    def test_create(self) -> None:
        self.set_models(
            {
                "meeting/10": {"is_active_in_organization_id": 1},
                "personal_note/11": {"star": True, "meeting_id": 10},
                "speaker/12": {"meeting_id": 10},
                "chat_message/13": {"meeting_id": 10},
                "motion/14": {"meeting_id": 10},
            }
        )
        test_dict = {
            "user_id": 1,
            "meeting_id": 10,
            "comment": "test blablaba",
            "number": "XII",
            "structure_level": "A",
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
            "personal_note_ids": [11],
            "speaker_ids": [12],
            "supported_motion_ids": [14],
            "chat_message_ids": [13],
        }
        response = self.request("meeting_user.create", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/1", test_dict)

    def test_create_no_permission(self) -> None:
        self.set_models(
            {
                "meeting/10": {"is_active_in_organization_id": 1},
                "user/1": {"organization_management_level": None},
            }
        )
        response = self.request("meeting_user.create", {"meeting_id": 10, "user_id": 1})
        self.assert_status_code(response, 403)

    def test_create_permission_self_change_about_me(self) -> None:
        self.set_models(
            {
                "meeting/10": {"is_active_in_organization_id": 1},
                "user/1": {"organization_management_level": None},
            }
        )
        response = self.request(
            "meeting_user.create", {"meeting_id": 10, "user_id": 1, "about_me": "test"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/1", {"meeting_id": 10, "user_id": 1, "about_me": "test"}
        )
        self.assert_model_exists("meeting/10", {"meeting_user_ids": [1]})
        self.assert_model_exists("user/1", {"meeting_user_ids": [1]})

    def test_create_no_permission_change_some_fields(self) -> None:
        self.set_models(
            {
                "meeting/10": {"is_active_in_organization_id": 1},
                "user/1": {"organization_management_level": None},
            }
        )
        response = self.request(
            "meeting_user.create",
            {"meeting_id": 10, "user_id": 1, "about_me": "test", "number": "XXIII"},
        )
        self.assert_status_code(response, 403)
