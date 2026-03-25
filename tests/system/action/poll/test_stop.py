from decimal import Decimal
from typing import Any
from unittest.mock import Mock, patch

from openslides_backend.models.models import Poll
from openslides_backend.permissions.permissions import Permissions
from tests.system.util import CountDatastoreCalls, Profiler, performance

from .base_poll_test import BasePollTestCase
from .poll_test_mixin import PollTestMixin


class PollStopActionTest(PollTestMixin, BasePollTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.poll_data: dict[str, Any] = {
            "type": Poll.TYPE_NAMED,
            "pollmethod": "Y",
            "backend": "fast",
            "content_object_id": "topic/1",
            "state": Poll.STATE_STARTED,
            "meeting_id": 1,
            "title": "Poll 1",
            "onehundred_percent_base": Poll.ONEHUNDRED_PERCENT_BASE_Y,
        }

    @patch("openslides_backend.services.vote.adapter.VoteAdapter.clear")
    def test_stop_correct(self, clear: Mock) -> None:
        clear_called_on: list[int] = []

        def add_to_list(id_: int) -> None:
            clear_called_on.append(id_)

        clear.side_effect = add_to_list
        self.create_meeting()
        self.create_motion(1, 1)
        user1 = self.create_user_for_meeting(1)
        user2 = self.create_user_for_meeting(1)
        user3 = self.create_user_for_meeting(1)
        self.set_models(
            {
                "poll/1": {
                    **self.poll_data,
                    "content_object_id": "motion/1",
                    "pollmethod": "YN",
                    "entitled_group_ids": [1],
                },
                "group/1": {"poll_ids": [1]},
                "option/1": {"meeting_id": 1, "poll_id": 1},
                "meeting/1": {
                    "users_enable_vote_weight": True,
                    "poll_couple_countdown": True,
                    "poll_countdown_id": 1,
                    "users_enable_vote_delegations": True,
                    "present_user_ids": [user1, user2],
                },
                "projector_countdown/1": {
                    "title": "Countdown 1",
                    "running": True,
                    "default_time": 60,
                    "countdown_time": 30.0,
                    "meeting_id": 1,
                },
                f"user/{user1}": {"default_vote_weight": Decimal("2.000000")},
                f"user/{user2}": {"default_vote_weight": Decimal("3.000000")},
                "meeting_user/1": {"vote_weight": Decimal("2.600000")},
                "meeting_user/2": {"vote_weight": Decimal("3.600000")},
                "meeting_user/3": {
                    "vote_weight": Decimal("4.600000"),
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
        self.assert_model_exists(
            "projector_countdown/1",
            {
                "running": False,
                "countdown_time": 60,
            },
        )
        self.assert_model_exists(
            "poll/1",
            {
                "voted_ids": [2, 4],
                "state": Poll.STATE_FINISHED,
                "votescast": Decimal("2.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votesvalid": Decimal("7.200000"),
                "entitled_users_at_stop": [
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
                ],
            },
        )
        # test history
        self.assert_history_information("motion/1", ["Voting stopped"])
        assert clear_called_on == [1]

    def test_stop_assignment_poll(self) -> None:
        self.create_meeting()
        self.create_assignment(1, 1)
        self.set_models(
            {
                "poll/1": {
                    **self.poll_data,
                    "content_object_id": "assignment/1",
                    "pollmethod": "YN",
                },
            }
        )
        self.start_poll(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("assignment/1", ["Ballot stopped"])

    def test_stop_entitled_users_at_stop_user_only_once(self) -> None:
        self.create_meeting()
        self.create_motion(1, 1)
        self.create_user("User2")
        self.set_user_groups(2, [2, 3])
        self.set_models(
            {
                "poll/1": {
                    **self.poll_data,
                    "content_object_id": "motion/1",
                    "entitled_group_ids": [3, 4],
                },
                "meeting/1": {"present_user_ids": [2]},
                "group/2": {"poll_ids": [1]},
                "group/3": {"poll_ids": [1]},
            }
        )
        self.start_poll(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "entitled_users_at_stop": [
                    {
                        "voted": False,
                        "present": True,
                        "user_id": 2,
                        "vote_delegated_to_user_id": None,
                    },
                ]
            },
        )

    def test_stop_entitled_users_not_present(self) -> None:
        self.create_meeting()
        self.create_motion(1, 1)
        user2 = self.create_user_for_meeting(1)
        user3 = self.create_user_for_meeting(1)
        self.set_user_groups(user2, [1])
        self.set_user_groups(user3, [3])
        self.set_models(
            {
                "poll/1": {**self.poll_data, "content_object_id": "motion/1"},
                "group/1": {"poll_ids": [1]},
            }
        )
        self.start_poll(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "entitled_users_at_stop": [
                    {
                        "voted": False,
                        "present": False,
                        "user_id": 2,
                        "vote_delegated_to_user_id": None,
                    },
                ]
            },
        )

    def test_stop_entitled_users_with_delegations(self) -> None:
        self.create_meeting(meeting_data={"users_enable_vote_delegations": True})
        self.create_motion(1, 1)
        user2 = self.create_user_for_meeting(1)
        user3 = self.create_user_for_meeting(1)
        self.set_user_groups(user2, [1])
        self.set_user_groups(user3, [3])
        self.set_models(
            {
                "poll/1": {**self.poll_data, "content_object_id": "motion/1"},
                "group/1": {"poll_ids": [1]},
                "meeting_user/1": {"vote_delegated_to_id": 2},
            }
        )
        self.start_poll(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "entitled_users_at_stop": [
                    {
                        "voted": False,
                        "present": False,
                        "user_id": 2,
                        "vote_delegated_to_user_id": 3,
                    },
                ]
            },
        )

    def test_stop_entitled_users_with_delegations_turned_off(self) -> None:
        self.create_meeting(meeting_data={"users_enable_vote_delegations": False})
        self.create_motion(1, 1)
        user2 = self.create_user_for_meeting(1)
        user3 = self.create_user_for_meeting(1)
        self.set_user_groups(user2, [1])
        self.set_user_groups(user3, [3])
        self.set_models(
            {
                "poll/1": {**self.poll_data, "content_object_id": "motion/1"},
                "group/1": {"poll_ids": [1]},
                "meeting_user/1": {"vote_delegated_to_id": 2},
            }
        )
        self.start_poll(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "entitled_users_at_stop": [
                    {
                        "voted": False,
                        "present": False,
                        "user_id": 2,
                        "vote_delegated_to_user_id": None,
                    },
                ]
            },
        )

    def test_stop_published(self) -> None:
        self.create_meeting()
        self.create_motion(1, 1)
        self.set_models(
            {
                "poll/1": {
                    **self.poll_data,
                    "content_object_id": "motion/1",
                    "state": Poll.STATE_PUBLISHED,
                },
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
        self.create_meeting()
        self.create_motion(1, 1)
        self.set_models(
            {
                "poll/1": {
                    **self.poll_data,
                    "content_object_id": "motion/1",
                    "state": Poll.STATE_CREATED,
                }
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
        self.create_meeting()
        self.create_topic(1, 1)
        self.set_models({"poll/1": self.poll_data})
        self.start_poll(1)
        self.base_permission_test({}, "poll.stop", {"id": 1})

        assert clear_called_on == []

    def test_stop_permissions(self) -> None:
        self.create_meeting()
        self.create_topic(1, 1)
        self.set_models({"poll/1": self.poll_data})
        self.start_poll(1)
        self.base_permission_test(
            {},
            "poll.stop",
            {"id": 1},
            Permissions.Poll.CAN_MANAGE,
        )

    def test_stop_permissions_locked_meeting(self) -> None:
        self.create_meeting()
        self.create_topic(1, 1)
        self.set_models({"poll/1": self.poll_data})
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
        self.assert_model_exists("poll/1", {"voted_ids": user_ids})
        assert counter.calls == 63

    @performance
    def test_stop_performance(self) -> None:
        user_ids = self.prepare_users_and_poll(3)

        with Profiler("test_stop_performance.prof"):
            response = self.request("poll.stop", {"id": 1})

        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll["voted_ids"] == user_ids
