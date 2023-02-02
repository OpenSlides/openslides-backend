from tests.system.action.base import BaseActionTestCase


class PollCandidateTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "meeting_1",
                    "is_active_in_organization_id": 1,
                    "poll_candidate_list_ids": [2],
                },
                "poll_candidate_list/2": {"meeting_id": 1},
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
