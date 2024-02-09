from typing import Any

from openslides_backend.models.models import Poll
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from .base_poll_test import BasePollTestCase


class VotePollBaseTestClass(BasePollTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "meeting/1": {
                    "name": "my meeting",
                    "poll_couple_countdown": True,
                    "poll_countdown_id": 11,
                    "is_active_in_organization_id": 1,
                    "group_ids": [1],
                    "meeting_user_ids": [11],
                    "present_user_ids": [1],
                },
                "projector_countdown/11": {
                    "default_time": 60,
                    "running": False,
                    "countdown_time": 60,
                    "meeting_id": 1,
                },
                "group/1": {"meeting_user_ids": [11]},
                "option/1": {"meeting_id": 1, "poll_id": 1},
                "option/2": {"meeting_id": 1, "poll_id": 1},
                "user/1": {
                    "is_present_in_meeting_ids": [1],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [1],
                },
                "assignment/1": {
                    "title": "test_assignment_tcLT59bmXrXif424Qw7K",
                    "open_posts": 1,
                    "meeting_id": 1,
                },
                "poll/1": {
                    "content_object_id": "assignment/1",
                    "title": "test_title_04k0y4TwPLpJKaSvIGm1",
                    "state": Poll.STATE_CREATED,
                    "meeting_id": 1,
                    "option_ids": [1, 2],
                    "entitled_group_ids": [1],
                    "votesinvalid": "0.000000",
                    "votesvalid": "0.000000",
                    "votescast": "0.000000",
                    "backend": "fast",
                    **self.get_poll_data(),
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
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assertNotIn("crypt_key", poll)
        self.assertNotIn("crypt_signature", poll)
        self.assert_model_not_exists("vote/1")
        # test history
        self.assert_history_information("assignment/1", ["Ballot started"])
        # test that votes can be given
        response = self.vote_service.vote({"id": 1, "value": {"1": "Y"}})
        self.assert_status_code(response, 200)

    def test_start_motion_poll(self) -> None:
        self.set_models(
            {
                "poll/1": {"content_object_id": "motion/1"},
                "motion/1": {"meeting_id": 1},
            }
        )
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
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assertNotIn("crypt_key", poll)
        self.assertNotIn("crypt_signature", poll)
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
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assertNotIn("crypt_key", poll)
        self.assertNotIn("crypt_signature", poll)
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
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assertNotIn("crypt_key", poll)
        self.assertNotIn("crypt_signature", poll)
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
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assertNotIn("crypt_key", poll)
        self.assertNotIn("crypt_signature", poll)
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
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assertNotIn("crypt_key", poll)
        self.assertNotIn("crypt_signature", poll)
        self.assert_model_not_exists("vote/1")


class VotePollCryptographicYNA(VotePollBaseTestClass):
    def get_poll_data(self) -> Dict[str, Any]:
        return {
            "pollmethod": "YNA",
            "type": Poll.TYPE_CRYPTOGRAPHIC,
        }

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assertIn("crypt_key", poll)
        self.assertIn("crypt_signature", poll)
        self.assert_model_not_exists("vote/1")


class VotePollCryptographicY(VotePollBaseTestClass):
    def get_poll_data(self) -> Dict[str, Any]:
        return {
            "pollmethod": "Y",
            "type": Poll.TYPE_CRYPTOGRAPHIC,
        }

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assertIn("crypt_key", poll)
        self.assertIn("crypt_signature", poll)
        self.assert_model_not_exists("vote/1")


class VotePollCryptographicN(VotePollBaseTestClass):
    def get_poll_data(self) -> Dict[str, Any]:
        return {
            "pollmethod": "N",
            "type": Poll.TYPE_CRYPTOGRAPHIC,
        }

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assertIn("crypt_key", poll)
        self.assertIn("crypt_signature", poll)
        self.assert_model_not_exists("vote/1")
