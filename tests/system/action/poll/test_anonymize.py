from tests.system.action.base import BaseActionTestCase


class PollAnonymizeActionTest(BaseActionTestCase):
    def test_anonymize(self) -> None:
        self.create_model("meeting/1", {})
        self.create_model(
            "poll/1",
            {
                "description": "test",
                "option_ids": [1],
                "global_option_id": 2,
                "meeting_id": 1,
            },
        )
        self.create_model("option/1", {"vote_ids": [1], "meeting_id": 1})
        self.create_model("option/2", {"vote_ids": [2], "meeting_id": 1})
        self.create_model("vote/1", {"user_id": 1, "meeting_id": 1})
        self.create_model("vote/2", {"user_id": 1, "meeting_id": 1})
        self.update_model("user/1", {"vote_$_ids": ["1"], "vote_$1_ids": [1, 2]})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.anonymize",
                    "data": [{"id": 1}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("description") == "test"
        for fqid in ("vote/1", "vote/2"):
            vote = self.get_model(fqid)
            assert vote.get("user_id") is None
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ['1']
        assert user.get("vote_$1_ids") == []
