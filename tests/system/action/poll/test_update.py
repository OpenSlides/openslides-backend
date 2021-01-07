import openslides_backend.action.actions  # noqa
from tests.system.action.base import BaseActionTestCase


class PollUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model("poll/1", {"state": 2, "type": "named"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.update",
                    "data": [
                        {
                            "id": 1,
                            "title": "test",
                            "description": "test2",
                            "onehundred_percent_base": "Y",
                            "majority_method": "simple",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("title") == "test"
        assert poll.get("description") == "test2"
        assert poll.get("onehundred_percent_base") == "Y"
        assert poll.get("majority_method") == "simple"

    def test_catch_not_allowed(self) -> None:
        self.create_model("poll/1", {"state": 2, "type": "named"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.update",
                    "data": [
                        {
                            "id": 1,
                            "pollmethod": "Y",
                            "type": "analog",
                            "min_votes_amount": 1,
                            "max_votes_amount": 1,
                            "global_yes": False,
                            "global_no": True,
                            "global_abstain": True,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert (
            "Following options are not allowed in this state and type: "
            "pollmethod, type, min_votes_amount, max_votes_amount, global_yes,"
            " global_no, global_abstain"
        ) in response.data.decode()

    def test_optional_state_created(self) -> None:
        self.create_model("poll/1", {"state": 1, "type": "named"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.update",
                    "data": [
                        {
                            "id": 1,
                            "pollmethod": "Y",
                            "type": "analog",
                            "min_votes_amount": 1,
                            "max_votes_amount": 1,
                            "global_yes": False,
                            "global_no": True,
                            "global_abstain": True,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("pollmethod") == "Y"
        assert poll.get("type") == "analog"
        assert poll.get("min_votes_amount") == 1
        assert poll.get("max_votes_amount") == 1
        assert poll.get("global_yes") is False
        assert poll.get("global_no") is True
        assert poll.get("global_abstain") is True

    def test_not_allowed_for_analog(self) -> None:
        self.create_model("poll/1", {"state": 2, "type": "analog"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.update",
                    "data": [{"id": 1, "entitled_group_ids": []}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert (
            "Following options are not allowed in this state and type: "
            "entitled_group_ids"
        ) in response.data.decode()

    def test_not_allowed_for_non_analog(self) -> None:
        self.create_model("poll/1", {"state": 2, "type": "named"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.update",
                    "data": [
                        {
                            "id": 1,
                            "votesvalid": "10.000000",
                            "votesinvalid": "11.000000",
                            "votescast": "3.000000",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert (
            "Following options are not allowed in this state and type: "
            "votesvalid, votesinvalid, votescast"
        ) in response.data.decode()
