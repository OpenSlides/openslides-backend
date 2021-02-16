from openslides_backend.models.models import Poll
from tests.system.action.base import BaseActionTestCase


class PollStartActionTest(BaseActionTestCase):
    def test_start_correct(self) -> None:
        self.create_model("poll/1", {"state": "created"})
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        # check if the state has been changed to 2 (Started).
        poll = self.get_model("poll/1")
        assert poll.get("state") == "started"

    def test_start_wrong_state(self) -> None:
        self.create_model("poll/1", {"state": "published"})
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "published"
        assert (
            "Cannot start poll 1, because it is not in state created."
            in response.data.decode()
        )


class VotePollBaseTestClass(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_model(
            "assignment/1",
            dict(
                title="test_assignment_tcLT59bmXrXif424Qw7K",
                open_posts=1,
                candidate_ids=[1],
            ),
        )
        self.create_poll()
        self.create_model("meeting/113", {"name": "my meeting"})
        self.create_model("group/1", {"user_ids": [1]})
        self.create_model("option/1", {"meeting_id": 113, "poll_id": 1})
        self.create_model("option/2", {"meeting_id": 113, "poll_id": 1})
        self.update_model(
            "user/1",
            {
                "is_present_in_meeting_ids": [113],
                "group_$113_ids": [1],
                "group_$_ids": ["113"],
            },
        )

    def create_poll(self) -> None:
        # has to be implemented by subclasses
        raise NotImplementedError()

    def start_poll(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED})

    def add_candidate(self) -> None:
        self.create_model("option/3", {"meeting_id": 113, "poll_id": 1})
        self.update_model("poll/1", {"option_ids": [1, 2, 3]})


class VotePollOS3AnalogYNA(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_04k0y4TwPLpJKaSvIGm1",
                pollmethod="YNA",
                type=Poll.TYPE_ANALOG,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
                votesinvalid="0.000000",
                votesvalid="0.000000",
                votescast="0.000000",
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", dict(id=1))
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assert_model_not_exists("vote/1")


class VotePollOS3NamedYNA(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_OkHAIvOSIcpFnCxbaL6v",
                pollmethod="YNA",
                type=Poll.TYPE_NAMED,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
                votesinvalid="0.000000",
                votesvalid="0.000000",
                votescast="0.000000",
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assert_model_not_exists("vote/1")


class VotePollOS3NamedY(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_Zrvh146QAdq7t6iSDwZk",
                pollmethod="Y",
                type=Poll.TYPE_NAMED,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
                votesinvalid="0.000000",
                votesvalid="0.000000",
                votescast="0.000000",
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assert_model_not_exists("vote/1")


class VotePollOS3NamedN(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_4oi49ckKFk39SDIfj30s",
                pollmethod="N",
                type=Poll.TYPE_NAMED,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
                votesinvalid="0.000000",
                votesvalid="0.000000",
                votescast="0.000000",
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assert_model_not_exists("vote/1")


class VotePollOS3PseudoanonymousYNA(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_OkHAIvOSIcpFnCxbaL6v",
                pollmethod="YNA",
                type=Poll.TYPE_PSEUDOANONYMOUS,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
                votesinvalid="0.000000",
                votesvalid="0.000000",
                votescast="0.000000",
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assert_model_not_exists("vote/1")


class VotePollOS3PseudoanonymousY(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_Zrvh146QAdq7t6iSDwZk",
                pollmethod="Y",
                type=Poll.TYPE_PSEUDOANONYMOUS,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
                votesinvalid="0.000000",
                votesvalid="0.000000",
                votescast="0.000000",
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assert_model_not_exists("vote/1")


class VotePollOS3PseudoAnonymousN(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_wWPOVJgL9afm83eamf3e",
                pollmethod="N",
                type=Poll.TYPE_PSEUDOANONYMOUS,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
                votesinvalid="0.000000",
                votesvalid="0.000000",
                votescast="0.000000",
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assert_model_not_exists("vote/1")
