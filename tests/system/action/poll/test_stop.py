import inspect
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from importlib import import_module
from time import sleep
from typing import Any
from unittest.mock import Mock, patch

import pytest
from psycopg.errors import DatabaseError

from openslides_backend.models.models import Poll
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.services.postgresql.db_connection_handling import (
    ConnectionContext,
)
from tests.system.action.lock import pytest_thread_local
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
        u_ids = []
        for i in range(len(user_ids)):
            u_ids.append(
                self.assert_model_exists(f"vote/{i+1}", {"meeting_id": 1})["user_id"]
            )
        assert sorted(u_ids) == sorted(user_ids)
        self.assert_model_not_exists(f"vote/{len(user_ids)+1}")
        assert counter.calls == 24

    @pytest.mark.skip("Takes too long for regular testing")
    def test_stop_with_more_users_than_vote_amount_steps(self) -> None:
        user_ids = self.prepare_users_and_poll(1003)
        response = self.request("poll.stop", {"id": 1})

        self.assert_status_code(response, 200)
        self.assert_model_exists("poll/1", {"voted_ids": user_ids})
        u_ids = []
        for i in range(len(user_ids)):
            u_ids.append(
                self.assert_model_exists(f"vote/{i+1}", {"meeting_id": 1})["user_id"]
            )
        assert sorted(u_ids) == sorted(user_ids)
        self.assert_model_not_exists(f"vote/{len(user_ids)+1}")

    @performance
    def test_stop_performance(self) -> None:
        user_ids = self.prepare_users_and_poll(3)

        with Profiler("test_stop_performance.prof"):
            response = self.request("poll.stop", {"id": 1})

        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll["voted_ids"] == user_ids

    def test_stop_race_condition1(self) -> None:
        """
        Asserts that the on_success method of poll.stop isn't called in case of a exception at the end of transaction.
        """
        pytest_thread_local.name = "MainThread_RC"
        self.set_thread_watch_timeout(1)
        self.env.vars["ACTION_MAX_RETRIES"] = "1"

        self.create_meeting(1, {"poll_couple_countdown": False})
        self.create_topic(1, 1)
        self.set_models(
            {
                "poll/1": self.poll_data,
                "group/1": {
                    "poll_ids": [1],
                    "permissions": ["poll.can_manage"],
                },
            }
        )

        self.start_poll(1)
        user_id = self.create_user_for_meeting(1)
        self.login(user_id)
        self.vote_service.vote({"id": 1, "value": {"1": "Y"}})

        with patch.object(self.vote_service, "clear", autospec=True) as mock_clear:
            with monkeypatch_get_new_os_conn():
                self.request("poll.stop", {"id": 1})
            mock_clear.assert_not_called()


hr_calls = 0


@contextmanager
def monkeypatch_get_new_os_conn() -> Iterator[None]:
    """
    Patches get_new_os_conn to further patch the ConnectionContext.
    """
    module = import_module("openslides_backend.action.action_handler")
    module.get_new_os_conn_original = module.get_new_os_conn  # type: ignore [attr-defined]
    module.get_new_os_conn = counting_get_new_os_conn  # type: ignore [attr-defined]
    try:
        yield
    finally:
        module.get_new_os_conn = module.get_new_os_conn_original  # type: ignore [attr-defined]
        delattr(module, "get_new_os_conn_original")


def counting_get_new_os_conn() -> ConnectionContext:  # type: ignore [attr-defined]
    """
    Wraps the __exit__ of the ConnectionContext to stall the thread and raise a DeadlockDetected exception.
    """
    global hr_calls

    def raise_exception(*args, **kwargs) -> None:  # type: ignore [no-untyped-def]
        """
        Should only be called by handle request on the second entering of the
        connection context but may be called by other functions too.
        """
        sleep(1.1)
        caller = inspect.stack()[1]
        if caller.function == "handle_request":
            ConnectionContext.original_exit(*args, **kwargs)  # type: ignore [attr-defined]
            ConnectionContext.__exit__ = ConnectionContext.original_exit  # type: ignore [method-assign,attr-defined]
            delattr(ConnectionContext, "original_exit")
            raise DatabaseError("WAAAAHH!!!!")
        else:
            ConnectionContext.__exit__(*args, **kwargs)

    nested_patch = False
    caller = inspect.stack()[1]
    if caller.function == "handle_request":
        # count in function context
        hr_calls += 1
        if hr_calls == 2:
            nested_patch = True
    module = import_module("openslides_backend.action.action_handler")
    if nested_patch:
        ConnectionContext.original_exit = ConnectionContext.__exit__  # type: ignore [attr-defined]
        ConnectionContext.__exit__ = raise_exception  # type: ignore[method-assign]
    return module.get_new_os_conn_original()  # type: ignore[method-assign]
