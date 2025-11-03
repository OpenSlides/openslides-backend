import threading

import pytest

from openslides_backend.action.action_handler import ActionHandler
from tests.system.action.base import ACTION_URL, BaseActionTestCase
from tests.system.action.lock import (
    monkeypatch_datastore_adapter_write,
    pytest_thread_local,
)


class MotionCreateActionTestSequentialNumber(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)
        self.set_user_groups(1, [222])

    def create_workflow(self, workflow_id: int = 12, meeting_id: int = 222) -> None:
        state_id = workflow_id + 100

        self.set_models(
            {
                f"motion_workflow/{workflow_id}": {
                    "name": f"motion_workflow{workflow_id}",
                    "first_state_id": state_id,
                    "meeting_id": meeting_id,
                },
                f"motion_state/{state_id}": {
                    "name": f"motion_state{state_id}",
                    "weight": state_id,
                    "workflow_id": workflow_id,
                    "meeting_id": meeting_id,
                },
            }
        )

    def test_create_sequential_numbers(self) -> None:
        response = self.request(
            "motion.create",
            {
                "title": "motion_title",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"sequential_number": 1})

        response = self.request(
            "motion.create",
            {
                "title": "motion_title2",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
            },
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"sequential_number": 2})

    def test_create_sequential_numbers_2meetings(self) -> None:
        self.create_meeting(225)
        response = self.request(
            "motion.create",
            {
                "title": "motion_title",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"sequential_number": 1})

        response = self.request(
            "motion.create",
            {
                "title": "motion_title",
                "meeting_id": 225,
                "workflow_id": 225,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"sequential_number": 1})

    def test_create_sequential_numbers_deleted_motion(self) -> None:
        response = self.request(
            "motion.create",
            {
                "title": "motion_title",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"sequential_number": 1})

        response = self.request("motion.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion/1")

        response = self.request(
            "motion.create",
            {
                "title": "motion_title",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test2",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"sequential_number": 2})

    @pytest.mark.skip(
        "Seems to run into an infinite loop, probably since the database is broken. TODO: unskip once this is fixed"
    )
    def test_create_sequential_numbers_race_condition(self) -> None:
        """
        !!!We could delete this test or implement a switch-off for the action_worker procedure at all!!!

        The main thread in this testing function creates an instance of a threading.lock and acquires it.
        Thread1 will be started first, but should wait for the acquired lock after reading and before writing.
        Thread2 will be started later, but passes thread1, because do not acquire the lock.
        After finishing thread2 the lock will be released in main thread and thread1 could continue with it's writing part.

        The lock-object will be shared in threading.local(), instance created in lock.py.
        If possible you should pass as an argument to the thread function(s).
        """
        ActionHandler.MAX_RETRY = 3
        self.set_thread_watch_timeout(-2)
        pytest_thread_local.name = "MainThread_RC"
        self.create_meeting(222)
        self.set_user_groups(1, [222])
        self.create_workflow(workflow_id=12, meeting_id=222)
        self.create_workflow(workflow_id=13, meeting_id=222)

        with monkeypatch_datastore_adapter_write():
            testlock = threading.Lock()
            sync_event = threading.Event()
            thread1 = threading.Thread(
                target=thread_method,
                kwargs={
                    "test_instance": self,
                    "motion_title": "Interrupted motion",
                    "meeting_id": 222,
                    "workflow_id": 12,
                    "testlock": testlock,
                    "name": "Interrupted Thread",
                    "sync_event": sync_event,
                },
            )
            thread2 = threading.Thread(
                target=thread_method,
                kwargs={
                    "test_instance": self,
                    "motion_title": "Passing motion",
                    "meeting_id": 222,
                    "workflow_id": 13,
                    "testlock": None,
                    "name": "Passing Thread",
                },
            )

            testlock.acquire()
            thread1.start()
            sync_event.wait()
            thread2.start()
            thread2.join()  # Now it fails here
            testlock.release()
            thread1.join()

        self.assert_model_not_exists("motion/1")
        self.assert_model_exists("motion/2", {"sequential_number": 1})
        self.assert_model_exists("motion/3", {"sequential_number": 2})


def thread_method(
    test_instance: MotionCreateActionTestSequentialNumber,
    meeting_id: int,
    workflow_id: int,
    motion_title: str,
    testlock: threading.Lock,
    name: str,
    sync_event: threading.Event | None = None,
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
                "action": "motion.create",
                "data": [
                    {
                        "title": motion_title,
                        "meeting_id": meeting_id,
                        "workflow_id": workflow_id,
                        "text": "test",
                    }
                ],
            }
        ],
    )

    if sync_event and not sync_event.is_set() and response.status_code != 200:
        sync_event.set()
    test_instance.assert_status_code(response, 200)
