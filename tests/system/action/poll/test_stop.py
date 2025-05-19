from typing import Any
from unittest.mock import Mock, patch

from openslides_backend.models.models import Poll
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.util import CountDatastoreCalls, Profiler, performance

from .base_poll_test import BasePollTestCase
from .poll_test_mixin import PollTestMixin


class PollStopActionTest(PollTestMixin, BasePollTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            "topic/1": {
                "meeting_id": 1,
            },
            "poll/1": {
                "type": "named",
                "pollmethod": "Y",
                "backend": "fast",
                "content_object_id": "topic/1",
                "state": Poll.STATE_STARTED,
                "meeting_id": 1,
                "sequential_number": 1,
                "title": "Poll 1",
                "onehundred_percent_base": "Y",
            },
            "meeting/1": {"is_active_in_organization_id": 1},
        }

    @patch("openslides_backend.services.vote.adapter.VoteAdapter.clear")
    def test_stop_correct(self, clear: Mock) -> None:
        clear_called_on: list[int] = []

        def add_to_list(id_: int) -> None:
            clear_called_on.append(id_)

        clear.side_effect = add_to_list
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "motion/1": {
                    "meeting_id": 1,
                },
                "poll/1": {
                    "content_object_id": "motion/1",
                    "type": Poll.TYPE_NAMED,
                    "pollmethod": "YN",
                    "backend": "fast",
                    "state": Poll.STATE_STARTED,
                    "option_ids": [1],
                    "meeting_id": 1,
                    "entitled_group_ids": [1],
                    "onehundred_percent_base": "Y",
                    "sequential_number": 1,
                    "title": "Poll 1",
                },
                "option/1": {"meeting_id": 1, "poll_id": 1},
                "group/1": {"meeting_id": 1},
                "meeting/1": {
                    "users_enable_vote_weight": True,
                    "default_group_id": 1,
                    "poll_couple_countdown": True,
                    "poll_countdown_id": 1,
                    "is_active_in_organization_id": 1,
                    "group_ids": [1],
                    "users_enable_vote_delegations": True,
                },
                "projector_countdown/1": {
                    "running": True,
                    "default_time": 60,
                    "countdown_time": 30.0,
                    "meeting_id": 1,
                },
            }
        )
        user1 = self.create_user_for_meeting(1)
        user2 = self.create_user_for_meeting(1)
        user3 = self.create_user_for_meeting(1)
        self.set_models(
            {
                f"user/{user1}": {
                    "meeting_user_ids": [1],
                    "default_vote_weight": "2.000000",
                    "is_present_in_meeting_ids": [1],
                },
                f"user/{user2}": {
                    "meeting_user_ids": [2],
                    "default_vote_weight": "3.000000",
                    "is_present_in_meeting_ids": [1],
                },
                f"user/{user3}": {"meeting_user_ids": [3]},
                "meeting_user/1": {
                    "user_id": 2,
                    "vote_weight": "2.600000",
                    "vote_delegations_from_ids": [4],
                },
                "meeting_user/2": {
                    "user_id": 3,
                    "vote_weight": "3.600000",
                },
                "meeting_user/3": {
                    "user_id": 4,
                    "vote_weight": "4.600000",
                    "vote_delegated_to_id": 1,
                },
            }
        )
        self.start_poll(1)
        self.login(user1)
        response = self.vote_service.vote({"id": 1, "value": {"1": "Y"}})
        self.assert_status_code(response, 200)
        response = self.vote_service.vote(
            {"id": 1, "user_id": user3, "value": {"1": "N"}}
        )
        self.assert_status_code(response, 200)

        self.login(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        countdown = self.get_model("projector_countdown/1")
        assert countdown.get("running") is False
        assert countdown.get("countdown_time") == 60
        poll = self.get_model("poll/1")
        assert poll.get("voted_ids") == [2, 4]
        assert poll.get("state") == Poll.STATE_FINISHED
        assert poll.get("votescast") == "2.000000"
        assert poll.get("votesinvalid") == "0.000000"
        assert poll.get("votesvalid") == "7.200000"
        assert poll.get("entitled_users_at_stop") == [
            {
                "voted": True,
                "present": True,
                "user_id": user1,
                "vote_delegated_to_user_id": None,
            },
            {
                "voted": False,
                "present": True,
                "user_id": user2,
                "vote_delegated_to_user_id": None,
            },
            {
                "voted": True,
                "present": False,
                "user_id": user3,
                "vote_delegated_to_user_id": user1,
            },
        ]
        # test history
        self.assert_history_information("motion/1", ["Voting stopped"])
        assert clear_called_on == [1]

    def test_stop_assignment_poll(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "assignment/1": {
                    "meeting_id": 1,
                },
                "poll/1": {
                    "content_object_id": "assignment/1",
                    "type": Poll.TYPE_NAMED,
                    "pollmethod": "YN",
                    "backend": "fast",
                    "state": Poll.STATE_STARTED,
                    "meeting_id": 1,
                    "onehundred_percent_base": "Y",
                    "sequential_number": 1,
                    "title": "Poll 1",
                },
            }
        )
        self.start_poll(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("assignment/1", ["Ballot stopped"])

    def test_stop_entitled_users_at_stop_user_only_once(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "meeting_id": 1,
                },
                "poll/1": {
                    "type": "named",
                    "pollmethod": "Y",
                    "backend": "fast",
                    "content_object_id": "motion/1",
                    "state": Poll.STATE_STARTED,
                    "meeting_id": 1,
                    "entitled_group_ids": [3, 4],
                    "onehundred_percent_base": "Y",
                    "sequential_number": 1,
                    "title": "Poll 1",
                },
                "user/2": {
                    "is_present_in_meeting_ids": [1],
                    "meeting_user_ids": [1],
                },
                "meeting_user/1": {
                    "user_id": 2,
                    "meeting_id": 1,
                    "group_ids": [3, 4],
                },
                "group/3": {"meeting_user_ids": [1]},
                "group/4": {"meeting_user_ids": [1]},
                "meeting/1": {
                    "group_ids": [3, 4],
                    "meeting_user_ids": [1],
                    "is_active_in_organization_id": 1,
                },
            }
        )
        self.start_poll(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("entitled_users_at_stop") == [
            {
                "voted": False,
                "present": True,
                "user_id": 2,
                "vote_delegated_to_user_id": None,
            },
        ]

    def test_stop_entitled_users_not_present(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "meeting_id": 1,
                },
                "poll/1": {
                    "type": "named",
                    "pollmethod": "Y",
                    "backend": "fast",
                    "content_object_id": "motion/1",
                    "state": Poll.STATE_STARTED,
                    "meeting_id": 1,
                    "entitled_group_ids": [3],
                    "onehundred_percent_base": "Y",
                    "sequential_number": 1,
                    "title": "Poll 1",
                },
                "user/2": {
                    "meeting_user_ids": [12],
                    "meeting_ids": [1],
                },
                "meeting_user/12": {"user_id": 2, "meeting_id": 1, "group_ids": [3]},
                "user/3": {
                    "meeting_user_ids": [13],
                    "meeting_ids": [1],
                },
                "meeting_user/13": {"user_id": 3, "meeting_id": 1, "group_ids": [4]},
                "group/3": {"meeting_user_ids": [12], "meeting_id": 1},
                "group/4": {"meeting_user_ids": [13], "meeting_id": 1},
                "meeting/1": {
                    "user_ids": [2, 3],
                    "group_ids": [3, 4],
                    "meeting_user_ids": [12, 13],
                    "is_active_in_organization_id": 1,
                },
            }
        )
        self.start_poll(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("entitled_users_at_stop") == [
            {
                "voted": False,
                "present": False,
                "user_id": 2,
                "vote_delegated_to_user_id": None,
            },
        ]

    def test_stop_entitled_users_with_delegations(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "meeting_id": 1,
                },
                "poll/1": {
                    "type": "named",
                    "pollmethod": "Y",
                    "backend": "fast",
                    "content_object_id": "motion/1",
                    "state": Poll.STATE_STARTED,
                    "meeting_id": 1,
                    "entitled_group_ids": [3],
                    "onehundred_percent_base": "Y",
                    "sequential_number": 1,
                    "title": "Poll 1",
                },
                "user/2": {
                    "meeting_user_ids": [12],
                    "meeting_ids": [1],
                },
                "meeting_user/12": {
                    "user_id": 2,
                    "meeting_id": 1,
                    "group_ids": [3],
                    "vote_delegated_to_id": 13,
                },
                "user/3": {
                    "meeting_user_ids": [13],
                    "meeting_ids": [1],
                },
                "meeting_user/13": {
                    "user_id": 3,
                    "meeting_id": 1,
                    "group_ids": [4],
                    "vote_delegations_from_ids": [12],
                },
                "group/3": {"meeting_user_ids": [12], "meeting_id": 1},
                "group/4": {"meeting_user_ids": [13], "meeting_id": 1},
                "meeting/1": {
                    "user_ids": [2, 3],
                    "group_ids": [3, 4],
                    "meeting_user_ids": [12, 13],
                    "is_active_in_organization_id": 1,
                    "users_enable_vote_delegations": True,
                },
            }
        )
        self.start_poll(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("entitled_users_at_stop") == [
            {
                "voted": False,
                "present": False,
                "user_id": 2,
                "vote_delegated_to_user_id": 3,
            },
        ]

    def test_stop_entitled_users_with_delegations_turned_off(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "meeting_id": 1,
                },
                "poll/1": {
                    "type": "named",
                    "pollmethod": "Y",
                    "backend": "fast",
                    "content_object_id": "motion/1",
                    "state": Poll.STATE_STARTED,
                    "meeting_id": 1,
                    "entitled_group_ids": [3],
                    "onehundred_percent_base": "Y",
                    "sequential_number": 1,
                    "title": "Poll 1",
                },
                "user/2": {
                    "meeting_user_ids": [12],
                    "meeting_ids": [1],
                },
                "meeting_user/12": {
                    "user_id": 2,
                    "meeting_id": 1,
                    "group_ids": [3],
                    "vote_delegated_to_id": 13,
                },
                "user/3": {
                    "meeting_user_ids": [13],
                    "meeting_ids": [1],
                },
                "meeting_user/13": {
                    "user_id": 3,
                    "meeting_id": 1,
                    "group_ids": [4],
                    "vote_delegations_from_ids": [12],
                },
                "group/3": {"meeting_user_ids": [12], "meeting_id": 1},
                "group/4": {"meeting_user_ids": [13], "meeting_id": 1},
                "meeting/1": {
                    "user_ids": [2, 3],
                    "group_ids": [3, 4],
                    "meeting_user_ids": [12, 13],
                    "is_active_in_organization_id": 1,
                    "users_enable_vote_delegations": False,
                },
            }
        )
        self.start_poll(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("entitled_users_at_stop") == [
            {
                "voted": False,
                "present": False,
                "user_id": 2,
                "vote_delegated_to_user_id": None,
            },
        ]

    def test_stop_published(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "meeting_id": 1,
                },
                "poll/1": {
                    "content_object_id": "motion/1",
                    "state": Poll.STATE_PUBLISHED,
                    "meeting_id": 1,
                },
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        assert poll.get("state") == Poll.STATE_PUBLISHED
        assert (
            "Cannot stop poll 1, because it is not in state started."
            in response.json["message"]
        )

    def test_stop_created(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "meeting_id": 1,
                },
                "poll/1": {
                    "content_object_id": "motion/1",
                    "state": Poll.STATE_CREATED,
                    "meeting_id": 1,
                },
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        assert poll.get("state") == Poll.STATE_CREATED
        assert (
            "Cannot stop poll 1, because it is not in state started."
            in response.json["message"]
        )

    @patch("openslides_backend.services.vote.adapter.VoteAdapter.clear")
    def test_stop_no_permissions(self, clear: Mock) -> None:
        clear_called_on: list[int] = []

        def add_to_list(id_: int) -> None:
            clear_called_on.append(id_)

        clear.side_effect = add_to_list
        self.set_models(self.test_models)
        self.start_poll(1)
        self.base_permission_test({}, "poll.stop", {"id": 1})

        assert clear_called_on == []

    def test_stop_permissions(self) -> None:
        self.set_models(self.test_models)
        self.start_poll(1)
        self.base_permission_test(
            {},
            "poll.stop",
            {"id": 1},
            Permissions.Poll.CAN_MANAGE,
        )

    def test_stop_permissions_locked_meeting(self) -> None:
        self.set_models(self.test_models)
        self.start_poll(1)
        self.base_locked_out_superadmin_permission_test(
            {},
            "poll.stop",
            {"id": 1},
        )

    def test_stop_datastore_calls(self) -> None:
        user_ids = self.prepare_users_and_poll(3)

        with CountDatastoreCalls() as counter:
            response = self.request("poll.stop", {"id": 1})

        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll["voted_ids"] == user_ids
        # always 12 plus len(user_ids) calls, dependent of user count
        assert counter.calls == 12 + len(user_ids)

    @performance
    def test_stop_performance(self) -> None:
        user_ids = self.prepare_users_and_poll(3)

        with Profiler("test_stop_performance.prof"):
            response = self.request("poll.stop", {"id": 1})

        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll["voted_ids"] == user_ids
