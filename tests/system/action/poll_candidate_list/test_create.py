from tests.system.action.base import BaseActionTestCase


class PollCandidateList(BaseActionTestCase):
    def test_create_correct(self) -> None:
        self.create_meeting()
        self.create_user("test1")
        self.create_user("test2")
        self.set_models({"option/4": {"meeting_id": 1}})
        response = self.request(
            "poll_candidate_list.create",
            {
                "option_id": 4,
                "meeting_id": 1,
                "entries": [{"user_id": 2, "weight": 1}, {"user_id": 3, "weight": 2}],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll_candidate_list/1",
            {"option_id": 4, "meeting_id": 1, "poll_candidate_ids": [1, 2]},
        )
        self.assert_model_exists(
            "poll_candidate/1",
            {"user_id": 2, "meeting_id": 1, "poll_candidate_list_id": 1, "weight": 1},
        )
        self.assert_model_exists(
            "poll_candidate/2",
            {"user_id": 3, "meeting_id": 1, "poll_candidate_list_id": 1, "weight": 2},
        )
        self.assert_model_exists("user/2", {"poll_candidate_ids": [1]})
        self.assert_model_exists("user/3", {"poll_candidate_ids": [2]})
        self.assert_model_exists(
            "meeting/1", {"poll_candidate_list_ids": [1], "poll_candidate_ids": [1, 2]}
        )
        self.assert_model_exists(
            "option/4", {"content_object_id": "poll_candidate_list/1"}
        )
