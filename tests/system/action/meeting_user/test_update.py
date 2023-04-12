from tests.system.action.base import BaseActionTestCase


class MeetingUserUpdate(BaseActionTestCase):
    def test_update(self) -> None:
        self.set_models(
            {
                "committee/1": {
                    "id": 1,
                    "meeting_ids": [10],
                },
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                    "personal_note_ids": [11],
                    "speaker_ids": [12],
                    "committee_id": 1,
                    "default_group_id": 22,
                },
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "personal_note/11": {"star": True, "meeting_id": 10},
                "speaker/12": {"meeting_id": 10},
                "motion/14": {"meeting_id": 10},
                "motion_submitter/15": {"meeting_id": 10},
                "assignment_candidate/16": {"meeting_id": 10},
                "projection/17": {"meeting_id": 10},
                "chat_message/13": {"meeting_id": 10},
                "vote/20": {"meeting_id": 10},
                "group/21": {"meeting_id": 10},
                "group/22": {"meeting_id": 10, "default_group_for_meeting_id": 10},
            }
        )
        test_dict = {
            "id": 5,
            "comment": "test bla",
            "number": "XII",
            "structure_level": "A",
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
            "personal_note_ids": [11],
            "speaker_ids": [12],
            "supported_motion_ids": [14],
            "motion_submitter_ids": [15],
            "assignment_candidate_ids": [16],
            "chat_message_ids": [13],
            "group_ids": [21],
        }
        response = self.request("meeting_user.update", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/5", test_dict)

    def test_update_no_permission(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                },
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "user/1": {"organization_management_level": None},
            }
        )
        response = self.request("meeting_user.update", {"id": 5, "number": "XX"})
        self.assert_status_code(response, 403)

    def test_update_permission_change_own_about_me(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                },
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "user/1": {"organization_management_level": None},
            }
        )
        response = self.request("meeting_user.update", {"id": 5, "about_me": "test"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/5", {"about_me": "test"})

    def test_update_no_permission_some_fields(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                },
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "user/1": {"organization_management_level": None},
            }
        )
        response = self.request(
            "meeting_user.update", {"id": 5, "about_me": "test", "number": "XX"}
        )
        self.assert_status_code(response, 403)
