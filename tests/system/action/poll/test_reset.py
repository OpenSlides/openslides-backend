from tests.system.action.base import BaseActionTestCase


class PollResetActionTest(BaseActionTestCase):
    def test_reset_correct(self) -> None:
        self.set_models(
            {
                "poll/1": {
                    "state": "started",
                    "option_ids": [1],
                    "global_option_id": 2,
                },
                "option/1": {"vote_ids": [1, 2], "poll_id": 1},
                "option/2": {"vote_ids": [3], "used_as_global_option_in_poll_id": 1},
                "vote/1": {"option_id": 1},
                "vote/2": {"option_id": 1},
                "vote/3": {"option_id": 2},
            }
        )

        response = self.request("poll.reset", {"id": 1})
        self.assert_status_code(response, 200)

        # check if the state has been changed to 1 (Created).
        poll = self.get_model("poll/1")
        assert poll.get("state") == "created"

        # check if the votes are deleted
        self.assert_model_deleted("vote/1")
        self.assert_model_deleted("vote/2")
        self.assert_model_deleted("vote/3")

        # check if the option.vote_ids fields are cleared
        option_1 = self.get_model("option/1")
        assert option_1.get("vote_ids") == []
        assert option_1.get("yes") == "0.000000"
        assert option_1.get("no") == "0.000000"
        assert option_1.get("abstain") == "0.000000"
        option_2 = self.get_model("option/2")
        assert option_2.get("vote_ids") == []
        assert option_2.get("yes") == "0.000000"
        assert option_2.get("no") == "0.000000"
        assert option_2.get("abstain") == "0.000000"
