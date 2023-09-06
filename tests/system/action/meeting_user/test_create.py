from tests.system.action.base import BaseActionTestCase


class MeetingUserCreate(BaseActionTestCase):
    def test_create(self) -> None:
        self.set_models(
            {
                "committee/1": {"meeting_ids": [10]},
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                    "group_ids": [21],
                },
                "personal_note/11": {"star": True, "meeting_id": 10},
                "speaker/12": {"meeting_id": 10},
                "chat_message/13": {"meeting_id": 10},
                "motion/14": {"meeting_id": 10},
                "motion_submitter/15": {"meeting_id": 10},
                "assignment_candidate/16": {"meeting_id": 10},
                "projection/17": {"meeting_id": 10},
                "vote/20": {"meeting_id": 10},
                "group/21": {"meeting_id": 10},
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
            "motion_submitter_ids": [15],
            "assignment_candidate_ids": [16],
            "chat_message_ids": [13],
            "group_ids": [21],
        }
        response = self.request("meeting_user.create", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/1", test_dict)
        self.assert_model_exists("user/1", {"committee_ids": [1]})
