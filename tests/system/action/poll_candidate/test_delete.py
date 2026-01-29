from tests.system.action.base import BaseActionTestCase


class PollCandidateDeleteTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "poll_candidate_list/2": {"meeting_id": 1},
                "option/1": {
                    "meeting_id": 1,
                    "content_object_id": "poll_candidate_list/2",
                },
                "poll_candidate/3": {
                    "meeting_id": 1,
                    "poll_candidate_list_id": 2,
                    "user_id": 1,
                    "weight": 1,
                },
            }
        )
        response = self.request("poll_candidate.delete", {"id": 3})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("poll_candidate/3")
        self.assert_model_exists("user/1", {"poll_candidate_ids": None})
        self.assert_model_exists("poll_candidate_list/2", {"poll_candidate_ids": None})
        self.assert_model_exists("meeting/1", {"poll_candidate_ids": None})
