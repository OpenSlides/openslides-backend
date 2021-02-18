from openslides_backend.models.models import Poll
from tests.system.action.base import BaseActionTestCase


class PollAnonymize(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {},
                "poll/1": {
                    "description": "test",
                    "option_ids": [1],
                    "global_option_id": 2,
                    "meeting_id": 1,
                    "state": Poll.STATE_FINISHED,
                },
                "option/1": {"vote_ids": [1], "meeting_id": 1},
                "option/2": {"vote_ids": [2], "meeting_id": 1},
                "vote/1": {"user_id": 1, "meeting_id": 1, "delegated_user_id": 1},
                "vote/2": {"user_id": 1, "meeting_id": 1, "delegated_user_id": 1},
                "user/1": {
                    "vote_$_ids": ["1"],
                    "vote_$1_ids": [1, 2],
                    "vote_delegated_vote_$_ids": ["1"],
                    "vote_delegated_vote_$1_ids": [1, 2],
                },
            }
        )

    def test_anonymize(self) -> None:
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("description") == "test"
        for fqid in ("vote/1", "vote/2"):
            vote = self.get_model(fqid)
            assert vote.get("user_id") is None
            assert vote.get("delegated_user_is") is None
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ["1"]
        assert user.get("vote_$1_ids") == []
        assert user.get("vote_delegated_vote_$_ids") == ["1"]
        assert user.get("vote_delegated_vote_$1_ids") == []

    def test_anonymize_wrong_state(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_CREATED})
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 400)
        for vote_fqid in ("vote/1", "vote/2"):
            vote = self.get_model(vote_fqid)
            assert vote.get("user_id")
            assert vote.get("delegated_user_id")

    def test_anonymize_wrong_type(self) -> None:
        self.update_model("poll/1", {"type": Poll.TYPE_ANALOG})
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 400)
        for vote_fqid in ("vote/1", "vote/2"):
            vote = self.get_model(vote_fqid)
            assert vote.get("user_id")
            assert vote.get("delegated_user_id")
