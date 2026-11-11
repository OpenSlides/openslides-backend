import threading
from decimal import Decimal
from time import sleep
from typing import Any
from unittest.mock import Mock, patch
import threading
from collections.abc import Iterator
from contextlib import contextmanager

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.shared.interfaces.write_request import WriteRequest

pytest_thread_local = threading.local()


import pytest

from openslides_backend.models.models import Poll
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import ACTION_URL
from tests.system.action.lock import (
    monkeypatch_datastore_adapter_write,
    pytest_thread_local,
)
from tests.system.util import CountDatastoreCalls, Profiler, performance

from .base_poll_test import BasePollTestCase
from .poll_test_mixin import PollTestMixin
from openslides_backend.action.actions.poll.mixins import StopControl


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


    def on_stop(self, instance: dict[str, Any]) -> None:  # type: ignore
        """
        Wraps the write of the datastore.adapter and stops a thread, if the testlock attribute is set thread-local.
        See example in test_create_sequential_numbers_race_condition
        """
        # if hasattr(pytest_thread_local, "testlock") and pytest_thread_local.testlock:
        #     if (
        #         hasattr(pytest_thread_local, "sync_event")
        #         and pytest_thread_local.sync_event
        #     ):
        #         pytest_thread_local.sync_event.set()
        #     with pytest_thread_local.testlock:
        #         self.on_stop_original()
        # else:
        # StopControl.on_stop_original(self, instance)
        sleep(3)
        print("### sleeeppppp!!!")
        raise Exception("WAAAAHH!!!!")

    @contextmanager
    def monkeypatch_on_stop(self) -> Iterator[None]:
        """
        Use a patched ExtendedDatabase.write in this context,
        which wraps the write with an optional lock from pytest_thread_local.testlock
        """
        StopControl.on_stop_original = StopControl.on_stop  # type: ignore
        StopControl.on_stop = self.on_stop  # type: ignore
        try:
            yield
        finally:
            StopControl.on_stop = StopControl.on_stop  # type: ignore
            delattr(StopControl, "on_stop_original")

    def test_stop_race_condition1(self) -> None:
        """
        The main thread in this testing function creates an instance of a threading.lock and acquires it.
        Thread1 will be started first, but should wait for the acquired lock after reading and before writing.
        Thread2 will be started later, but passes thread1, because it does not acquire the lock.
        After finishing of thread2 the lock will be released in the main thread and thread1 could continue with it's writing part.

        The lock-object will be shared in threading.local(), instance created in lock.py.
        If possible you should pass the lock as an argument to the thread function(s).
        """
        pytest_thread_local.name = "MainThread_RC"
        self.set_thread_watch_timeout(1)

        self.create_meeting(1, {"poll_couple_countdown": False})
        self.create_topic(1, 1)
        self.set_models(
            {
                "poll/1": self.poll_data,
                "group/1": {
                    "poll_ids": [1],
                    "permissions": ["poll.can_manage", "user.can_manage_presence"],
                },
            }
        )

        self.start_poll(1)
        # user_id = self.create_user_for_meeting(1)
        # self.login(user_id)
        # self.vote_service.vote({"id": 1, "value": {"1": "Y"}})
        # self.set_models({"meeting/1": {"present_user_ids": [user_id]}})

        # amount = 1000
        amount = 10
        for i in range(2, amount):
            user_id = self.create_user_for_meeting(1)
            self.login(user_id)
            self.vote_service.vote({"id": 1, "value": {"1": "Y"}})
        self.set_models({"meeting/1": {"present_user_ids": [*range(1, amount)]}})

        with self.monkeypatch_on_stop():
            self.request("poll.stop", {"id": 1})

        # self.assert_model_exists("poll/1", {"state": "finished"})
        self.assert_model_exists("poll/1", {"state": "started"})  # TODO uncomment when concurrency bug recreated.
        self.assert_model_exists(f"user/{user_id}", {"is_present_in_meeting_ids": None})



    def test_stop_race_condition2(self) -> None:
        """
        The main thread in this testing function creates an instance of a threading.lock and acquires it.
        Thread1 will be started first, but should wait for the acquired lock after reading and before writing.
        Thread2 will be started later, but passes thread1, because it does not acquire the lock.
        After finishing of thread2 the lock will be released in the main thread and thread1 could continue with it's writing part.

        The lock-object will be shared in threading.local(), instance created in lock.py.
        If possible you should pass the lock as an argument to the thread function(s).
        """
        pytest_thread_local.name = "MainThread_RC"
        self.set_thread_watch_timeout(1)

        self.create_meeting(1, {"poll_couple_countdown": False})
        self.create_topic(1, 1)
        self.set_models(
            {
                "poll/1": self.poll_data,
                "group/1": {
                    "poll_ids": [1],
                    "permissions": ["poll.can_manage", "user.can_manage_presence"],
                },
            }
        )

        self.start_poll(1)
        # user_id = self.create_user_for_meeting(1)
        # self.login(user_id)
        # self.vote_service.vote({"id": 1, "value": {"1": "Y"}})
        # self.set_models({"meeting/1": {"present_user_ids": [user_id]}})

        # amount = 1000
        amount = 10
        for i in range(2, amount):
            user_id = self.create_user_for_meeting(1)
            self.login(user_id)
            self.vote_service.vote({"id": 1, "value": {"1": "Y"}})
        self.set_models({"meeting/1": {"present_user_ids": [*range(1, amount)]}})

        with monkeypatch_datastore_adapter_write():
            testlock2 = threading.Lock()
            sync_event2 = threading.Event()
            testlock = threading.Lock()
            sync_event = threading.Event()
            thread1 = threading.Thread(
                target=thread_method_poll_stop,
                kwargs={
                    "test_instance": self,
                    "testlock": testlock,
                    "name": "Interrupted Thread",
                    "sync_event": sync_event,
                },
            )
            thread2 = threading.Thread(
                target=thread_method_is_present,
                kwargs={
                    "test_instance": self,
                    "name": "Passing Thread",
                    "user_id": user_id,
                    "sync_event": sync_event2,
                    "testlock": testlock2,
                },
            )

            testlock.acquire()
            thread1.start()
            sync_event.wait()
            # sleep(0.01)
            thread2.start()
            sync_event2.wait()
            testlock.release()
            sync_event.wait()
            testlock.release()
            testlock2.release()
            thread2.join()
            thread1.join()

        # self.assert_model_exists("poll/1", {"state": "finished"})
        self.assert_model_exists("poll/1", {"state": "started"})  # TODO uncomment when concurrency bug recreated.
        self.assert_model_exists(f"user/{user_id}", {"is_present_in_meeting_ids": None})


def thread_method_poll_stop(
    test_instance: PollStopActionTest,
    testlock: threading.Lock,
    name: str,
    sync_event: threading.Event,
) -> None:
    if testlock:
        pytest_thread_local.testlock = testlock
    if sync_event:
        pytest_thread_local.sync_event = sync_event
    pytest_thread_local.name = name
    response = test_instance.client.post(
        ACTION_URL,
        json=[
            {
                "action": "poll.stop",
                "data": [{"id": 1}],
            }
        ],
    )
    test_instance.connection.commit()

    if sync_event and not sync_event.is_set() and response.status_code != 200:
        sync_event.set()
    # test_instance.assert_status_code(response, 400)


def thread_method_is_present(
    test_instance: PollStopActionTest,
    name: str,
    user_id: int,
    testlock: threading.Lock,
    sync_event: threading.Event,
) -> None:
    pytest_thread_local.name = name
    if testlock:
        pytest_thread_local.testlock = testlock
    if sync_event:
        pytest_thread_local.sync_event = sync_event
    response = test_instance.client.post(
        ACTION_URL,
        json=[
            {
                "action": "user.set_present",
                "data": [{"id": user_id, "meeting_id": 1, "present": False}],
            }
        ],
    )
    test_instance.connection.commit()

    test_instance.assert_status_code(response, 200)
