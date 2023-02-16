from tests.system.action.base import BaseActionTestCase


class MeetingUserSetData(BaseActionTestCase):
    def test_set_data_with_meeting_user(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                    "personal_note_ids": [11],
                    "speaker_ids": [12],
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
            }
        )
        test_dict = {
            "meeting_id": 10,
            "user_id": 1,
            "comment": "test bla",
            "number": "XII",
            "structure_level": "A",
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
            "personal_note_ids": [11],
            "speaker_ids": [12],
            "supported_motion_ids": [14],
            "submitted_motion_ids": [15],
            "assignment_candidate_ids": [16],
            "projection_ids": [17],
            "chat_message_ids": [13],
            "vote_delegated_vote_ids": [20],
        }
        response = self.request("meeting_user.set_data", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/5", test_dict)

    def test_set_data_without_meeting_user(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [],
                    "personal_note_ids": [11],
                    "speaker_ids": [12],
                },
                "personal_note/11": {"star": True, "meeting_id": 10},
                "speaker/12": {"meeting_id": 10},
                "motion/14": {"meeting_id": 10},
                "motion_submitter/15": {"meeting_id": 10},
                "assignment_candidate/16": {"meeting_id": 10},
                "projection/17": {"meeting_id": 10},
                "chat_message/13": {"meeting_id": 10},
                "vote/20": {"meeting_id": 10},
            }
        )
        test_dict = {
            "meeting_id": 10,
            "user_id": 1,
            "comment": "test bla",
            "number": "XII",
            "structure_level": "A",
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
            "personal_note_ids": [11],
            "speaker_ids": [12],
            "supported_motion_ids": [14],
            "submitted_motion_ids": [15],
            "assignment_candidate_ids": [16],
            "projection_ids": [17],
            "chat_message_ids": [13],
            "vote_delegated_vote_ids": [20],
        }
        response = self.request("meeting_user.set_data", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/1", test_dict)
