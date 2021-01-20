from tests.system.action.base import BaseActionTestCase


class PollResetActionTest(BaseActionTestCase):
    def test_reset_correct(self) -> None:
        self.create_model(
            "poll/1", {"state": "started", "option_ids": [1], "global_option_id": 2}
        )
        self.create_model("option/1", {"vote_ids": [1, 2], "poll_id": 1})
        self.create_model(
            "option/2", {"vote_ids": [3], "used_as_global_option_in_poll_id": 1}
        )
        self.create_model("vote/1", {"option_id": 1})
        self.create_model("vote/2", {"option_id": 1})
        self.create_model("vote/3", {"option_id": 2})

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.reset",
                    "data": [{"id": 1}],
                }
            ],
        )
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
        option_2 = self.get_model("option/2")
        assert option_2.get("vote_ids") == []
