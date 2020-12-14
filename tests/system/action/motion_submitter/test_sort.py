import threading
from typing import cast

from tests.system.action.base import BaseActionTestCase
from tests.system.action.lock import (
    OSTestThread,
    monkeypatch_datastore_adapter_write,
    pytest_thread_local,
)


class MotionSubmitterSortActionTest(BaseActionTestCase):
    def test_sort_correct_1(self) -> None:
        self.create_model("motion/222", {})
        self.create_model("motion_submitter/31", {"motion_id": 222})
        self.create_model("motion_submitter/32", {"motion_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_submitter.sort",
                    "data": [{"motion_id": 222, "motion_submitter_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model_31 = self.get_model("motion_submitter/31")
        assert model_31.get("weight") == 2
        model_32 = self.get_model("motion_submitter/32")
        assert model_32.get("weight") == 1

    def test_sort_missing_model(self) -> None:
        self.create_model("motion/222", {})
        self.create_model("motion_submitter/31", {"motion_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_submitter.sort",
                    "data": [{"motion_id": 222, "motion_submitter_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Id 32 not in db_instances." in str(response.data)

    def test_sort_another_section_db(self) -> None:
        self.create_model("motion/222", {})
        self.create_model("motion_submitter/31", {"motion_id": 222})
        self.create_model("motion_submitter/32", {"motion_id": 222})
        self.create_model("motion_submitter/33", {"motion_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_submitter.sort",
                    "data": [{"motion_id": 222, "motion_submitter_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Additional db_instances found." in str(response.data)

    def test_sort_delete_submitter_correct(self) -> None:
        self.create_model("meeting/98", {"motion_submitter_ids": [31, 32, 33]})
        self.create_model(
            "motion/222",
            {
                "submitter_ids": [31, 32, 33],
                "meeting_id": 98,
            },
        )
        self.create_model(
            "motion_submitter/31",
            {
                "motion_id": 222,
                "meeting_id": 98,
            },
        )
        self.create_model(
            "motion_submitter/32",
            {
                "motion_id": 222,
                "meeting_id": 98,
            },
        )
        self.create_model(
            "motion_submitter/33",
            {
                "motion_id": 222,
                "meeting_id": 98,
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_submitter.sort",
                    "data": [{"motion_id": 222, "motion_submitter_ids": [33, 32, 31]}],
                },
                {
                    "action": "motion_submitter.delete",
                    "data": [{"id": 32}],
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/222", {"submitter_ids": [31, 33]})

    def test_sort_delete_submitter_fail(self) -> None:
        self.create_model("meeting/98", {"motion_submitter_ids": [31, 32, 33]})
        self.create_model(
            "motion/222",
            {
                "submitter_ids": [31, 32, 33],
                "meeting_id": 98,
            },
        )
        self.create_model(
            "motion_submitter/31",
            {
                "motion_id": 222,
                "meeting_id": 98,
            },
        )
        self.create_model(
            "motion_submitter/32",
            {
                "motion_id": 222,
                "meeting_id": 98,
            },
        )
        self.create_model(
            "motion_submitter/33",
            {
                "motion_id": 222,
                "meeting_id": 98,
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_submitter.delete",
                    "data": [{"id": 32}],
                },
                {
                    "action": "motion_submitter.sort",
                    "data": [{"motion_id": 222, "motion_submitter_ids": [33, 32, 31]}],
                },
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Model \\'motion_submitter/32\\' does not exist", str(response.data)
        )

    def test_sort_delete_race_condition(self) -> None:
        self.create_model("meeting/98", {"motion_submitter_ids": [31, 32]})
        self.create_model(
            "motion/222",
            {
                "submitter_ids": [31, 32],
                "meeting_id": 98,
            },
        )
        self.create_model(
            "motion_submitter/31",
            {
                "motion_id": 222,
                "meeting_id": 98,
            },
        )
        self.create_model(
            "motion_submitter/32",
            {
                "motion_id": 222,
                "meeting_id": 98,
            },
        )

        with monkeypatch_datastore_adapter_write():
            testlock = threading.Lock()
            sync_event = threading.Event()
            thread1 = OSTestThread(
                target=thread_method_sorting,
                kwargs={
                    "test_instance": self,
                    "testlock": testlock,
                    "name": "Interrupted Sorting Thread",
                    "sync_event": sync_event,
                },
            )
            thread2 = OSTestThread(
                target=thread_method_delete,
                kwargs={
                    "test_instance": self,
                    "name": "Passing Delete Thread",
                },
            )

            testlock.acquire()
            thread1.start()
            sync_event.wait()
            thread2.start()
            thread2.join()
            testlock.release()
            thread1.join()

        self.assert_model_locked_thrown_in_thread(thread1)
        self.assert_no_thread_exception(thread2)
        self.assert_thread_exception(thread1, "Id 32 not in db_instances")


def thread_method_sorting(
    test_instance: MotionSubmitterSortActionTest,
    testlock: threading.Lock,
    name: str,
    sync_event: threading.Event = None,
) -> None:
    if testlock:
        pytest_thread_local.testlock = testlock
    if sync_event:
        pytest_thread_local.sync_event = sync_event
    pytest_thread_local.count_model_locked = True
    pytest_thread_local.name = name
    response = test_instance.client.post(
        "/",
        json=[
            {
                "action": "motion_submitter.sort",
                "data": [{"motion_id": 222, "motion_submitter_ids": [32, 31]}],
            },
        ],
    )
    cast(OSTestThread, threading.current_thread()).check_response(response)


def thread_method_delete(
    test_instance: MotionSubmitterSortActionTest,
    name: str,
) -> None:
    pytest_thread_local.name = name
    response = test_instance.client.post(
        "/",
        json=[
            {
                "action": "motion_submitter.delete",
                "data": [{"id": 32}],
            },
        ],
    )
    cast(OSTestThread, threading.current_thread()).check_response(response)
