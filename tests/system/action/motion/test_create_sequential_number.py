import threading

import pytest

from openslides_backend.action.action_handler import ActionHandler
from tests.system.action.base import ACTION_URL, BaseActionTestCase
from tests.system.action.lock import (
    monkeypatch_datastore_adapter_write,
    pytest_thread_local,
)


class MotionCreateActionTestSequentialNumber(BaseActionTestCase):
    def create_workflow(self, workflow_id: int = 12, meeting_id: int = 222) -> None:
        state_id = workflow_id + 100
        state_str = str(state_id)

        self.create_model(
            "motion_workflow/" + str(workflow_id),
            {
                "name": "name_workflow1",
                "first_state_id": state_id,
                "state_ids": [state_id],
            },
        )
        self.create_model(
            "motion_state/" + state_str,
            {"name": "name_state" + state_str, "meeting_id": meeting_id},
        )

    def test_create_sequential_numbers(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1, "committee_id": 1},
                "user/1": {"meeting_ids": [222]},
            }
        )
        self.create_workflow()

        response = self.request(
            "motion.create",
            {
                "title": "motion_title",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        self.assertEqual(model.get("sequential_number"), 1)

        response = self.request(
            "motion.create",
            {
                "title": "motion_title2",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
            },
        )

        self.assert_status_code(response, 200)
        model = self.get_model("motion/2")
        self.assertEqual(model.get("sequential_number"), 2)

    def test_create_sequential_numbers_2meetings(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "meeting222",
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "meeting/223": {
                    "name": "meeting223",
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                },
                "user/1": {"meeting_ids": [222]},
            }
        )

        self.create_workflow()
        response = self.request(
            "motion.create",
            {
                "title": "motion_title",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        self.assertEqual(model.get("sequential_number"), 1)

        self.create_workflow(workflow_id=13, meeting_id=223)
        response = self.request(
            "motion.create",
            {
                "title": "motion_title",
                "meeting_id": 223,
                "workflow_id": 13,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/2")
        self.assertEqual(model.get("sequential_number"), 1)

    def test_create_sequential_numbers_deleted_motion(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1, "committee_id": 1},
                "user/1": {"meeting_ids": [222]},
            }
        )
        self.create_workflow()

        response = self.request(
            "motion.create",
            {
                "title": "motion_title",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        self.assertEqual(model.get("sequential_number"), 1)

        response = self.request("motion.delete", {"id": 1})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("meta_deleted")

        response = self.request(
            "motion.create",
            {
                "title": "motion_title",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test2",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/2")
        self.assertEqual(model.get("sequential_number"), 2)

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
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1, "committee_id": 1},
                "user/1": {"meeting_ids": [222]},
            }
        )
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
            sync_event.wait()  # This is where it fails
            thread2.start()
            thread2.join()
            testlock.release()
            thread1.join()

        self.assert_model_not_exists("motion/1")
        model2 = self.get_model("motion/2")
        model3 = self.get_model("motion/3")
        self.assertEqual(model2["sequential_number"], 1)
        self.assertEqual(model3["sequential_number"], 2)


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
