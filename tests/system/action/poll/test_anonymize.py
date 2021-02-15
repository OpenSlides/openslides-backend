from openslides_backend.models.models import Poll
from tests.system.action.base import BaseActionTestCase


class PollAnonymizeActionTest(BaseActionTestCase):
    def test_anonymize(self) -> None:
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


class AnonymizeOS3Poll(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_model(
            "assignment/1",
            {
                "title": "test_assignment_QLydMOqkyOHG68yZFJxl",
                "open_posts": 1,
                "candidate_ids": [1],
            },
        )
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_3LbUCNirKirpJhRHRxzW",
                pollmethod="YNA",
                type=Poll.TYPE_NAMED,
                state=Poll.STATE_FINISHED,
                option_ids=[11],
                meeting_id=113,
                voted_ids=[1, 2],
                votesvalid="2.000000",
                votesinvalid="0.000000",
                votescast="2.000000",
            ),
        )
        self.create_model(
            "option/11",
            {
                "meeting_id": 113,
                "poll_id": 1,
                "yes": "1.000000",
                "no": "1.000000",
                "abstain": "0.000000",
                "vote_ids": [1, 2],
            },
        )
        self.create_model("meeting/113", {"name": "my meeting"})

        self.create_model(
            "vote/1",
            dict(meeting_id=113, user_id=1, option_id=11, value="Y", weight="1.000000"),
        )
        self.update_model(
            "user/1",
            {
                "vote_$_ids": ["113"],
                "vote_$113_ids": [1],
            },
        )
        self.create_model(
            "user/2",
            {"username": "test_user_2", "vote_$113_ids": [2], "vote_$_ids": ["113"]},
        )
        self.create_model(
            "vote/2",
            dict(meeting_id=113, user_id=2, option_id=11, value="N", weight="1.000000"),
        )

    def test_anonymize_poll(self) -> None:
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "2.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "2.000000")
        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "1.000000")
        self.assertEqual(option.get("no"), "1.000000")
        self.assertEqual(option.get("abstain"), "0.000000")
        self.assertTrue(1 in poll.get("voted_ids", []))
        self.assertTrue(2 in poll.get("voted_ids", []))
        for vote_fqid in ("vote/1", "vote/2"):
            vote = self.get_model(vote_fqid)
            assert vote.get("user_id") is None

    def test_anonymize_wrong_state(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_CREATED})
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 400)
        for vote_fqid in ("vote/1", "vote/2"):
            vote = self.get_model(vote_fqid)
            assert vote.get("user_id")

    def test_anonymize_wrong_type(self) -> None:
        self.update_model("poll/1", {"type": Poll.TYPE_ANALOG})
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 400)
        for vote_fqid in ("vote/1", "vote/2"):
            vote = self.get_model(vote_fqid)
            assert vote.get("user_id")
