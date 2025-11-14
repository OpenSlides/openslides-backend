from decimal import Decimal
from typing import Any

from openslides_backend.models.models import Poll

from .base_poll_test import BasePollTestCase


class VotePollBaseTestClass(BasePollTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(meeting_data={"poll_couple_countdown": True})
        self.create_assignment(1, 1)
        self.set_user_groups(1, [1])
        self.set_models(
            {
                "meeting/1": {"present_user_ids": [1], "poll_countdown_id": 11},
                "projector_countdown/11": {
                    "title": "Countdown 11",
                    "default_time": 60,
                    "running": False,
                    "countdown_time": 60,
                    "meeting_id": 1,
                },
                "group/1": {"poll_ids": [1]},
                "option/1": {"meeting_id": 1, "poll_id": 1},
                "option/2": {"meeting_id": 1, "poll_id": 1},
                "poll/1": {
                    "content_object_id": "assignment/1",
                    "title": "test_title_04k0y4TwPLpJKaSvIGm1",
                    "state": Poll.STATE_CREATED,
                    "meeting_id": 1,
                    "votesinvalid": Decimal("0.000000"),
                    "votesvalid": Decimal("0.000000"),
                    "votescast": Decimal("0.000000"),
                    "backend": "fast",
                    **self.get_poll_data(),
                    "onehundred_percent_base": "YNA",
                },
            }
        )

    def get_poll_data(self) -> dict[str, Any]:
        # has to be implemented by subclasses
        raise NotImplementedError()


class VotePollAnalogYNA(VotePollBaseTestClass):
    def get_poll_data(self) -> dict[str, Any]:
        return {
            "pollmethod": "YNA",
            "type": Poll.TYPE_ANALOG,
        }

    def test_start_analog_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 400)
        assert (
            "Analog polls cannot be started. Please use poll.update instead to give votes."
            in response.json["message"]
        )
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_CREATED)


class VotePollNamedYNA(VotePollBaseTestClass):
    def get_poll_data(self) -> dict[str, Any]:
        return {
            "pollmethod": "YNA",
            "type": Poll.TYPE_NAMED,
        }

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "state": Poll.STATE_STARTED,
                "votesvalid": Decimal("0.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("0.000000"),
            },
        )
        self.assert_model_not_exists("vote/1")
        # test history
        self.assert_history_information("assignment/1", ["Ballot started"])
        # test that votes can be given
        response = self.vote_service.vote({"id": 1, "value": {"1": "Y"}})
        self.assert_status_code(response, 200)

    def test_start_motion_poll(self) -> None:
        self.create_motion(1, 1)
        self.set_models({"poll/1": {"content_object_id": "motion/1"}})
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/1", ["Voting started"])


class VotePollNamedY(VotePollBaseTestClass):
    def get_poll_data(self) -> dict[str, Any]:
        return {
            "pollmethod": "Y",
            "type": Poll.TYPE_NAMED,
        }

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "state": Poll.STATE_STARTED,
                "votesvalid": Decimal("0.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("0.000000"),
            },
        )
        self.assert_model_not_exists("vote/1")


class VotePollNamedN(VotePollBaseTestClass):
    def get_poll_data(self) -> dict[str, Any]:
        return {
            "pollmethod": "N",
            "type": Poll.TYPE_NAMED,
        }

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "state": Poll.STATE_STARTED,
                "votesvalid": Decimal("0.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("0.000000"),
            },
        )
        self.assert_model_not_exists("vote/1")


class VotePollPseudoanonymousYNA(VotePollBaseTestClass):
    def get_poll_data(self) -> dict[str, Any]:
        return {
            "pollmethod": "YNA",
            "type": Poll.TYPE_PSEUDOANONYMOUS,
        }

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "state": Poll.STATE_STARTED,
                "votesvalid": Decimal("0.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("0.000000"),
            },
        )
        self.assert_model_not_exists("vote/1")


class VotePollPseudoanonymousY(VotePollBaseTestClass):
    def get_poll_data(self) -> dict[str, Any]:
        return {
            "pollmethod": "Y",
            "type": Poll.TYPE_PSEUDOANONYMOUS,
        }

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "state": Poll.STATE_STARTED,
                "votesvalid": Decimal("0.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("0.000000"),
            },
        )
        self.assert_model_not_exists("vote/1")


class VotePollPseudoAnonymousN(VotePollBaseTestClass):
    def get_poll_data(self) -> dict[str, Any]:
        return {
            "pollmethod": "N",
            "type": Poll.TYPE_PSEUDOANONYMOUS,
        }

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "state": Poll.STATE_STARTED,
                "votesvalid": Decimal("0.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("0.000000"),
            },
        )
        self.assert_model_not_exists("vote/1")
