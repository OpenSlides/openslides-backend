from tests.system.action.base import BaseActionTestCase


class PollCandidateTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "poll_candidate_list/2": {"meeting_id": 1},
                "option/1": {
                    "meeting_id": 1,
                    "content_object_id": "poll_candidate_list/2",
                },
            }
        )
        response = self.request(
            "poll_candidate.create",
            {"user_id": 1, "poll_candidate_list_id": 2, "weight": 12, "meeting_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll_candidate/1",
            {"meeting_id": 1, "user_id": 1, "poll_candidate_list_id": 2, "weight": 12},
        )
        self.assert_model_exists("user/1", {"poll_candidate_ids": [1]})
        self.assert_model_exists("meeting/1", {"poll_candidate_ids": [1]})
        self.assert_model_exists("poll_candidate_list/2", {"poll_candidate_ids": [1]})
