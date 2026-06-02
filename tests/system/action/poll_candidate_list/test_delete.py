from tests.system.action.base import BaseActionTestCase


class PollCandidateListDeleteTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_meeting()
        self.create_user("test1")
        self.create_user("test2")
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
                "poll_candidate/4": {
                    "meeting_id": 1,
                    "poll_candidate_list_id": 2,
                    "user_id": 2,
                    "weight": 2,
                },
                "poll_candidate/5": {
                    "meeting_id": 1,
                    "poll_candidate_list_id": 2,
                    "user_id": 3,
                    "weight": 3,
                },
            }
        )
        response = self.request("poll_candidate_list.delete", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("poll_candidate_list/2")
        for poll_candidate_id in range(3, 6):
            self.assert_model_not_exists(f"poll_candidate/{poll_candidate_id}")
        for user_id in range(1, 4):
            self.assert_model_exists(f"user/{user_id}", {"poll_candidate_ids": None})
        self.assert_model_exists(
            "meeting/1", {"poll_candidate_list_ids": None, "poll_candidate_ids": None}
        )
