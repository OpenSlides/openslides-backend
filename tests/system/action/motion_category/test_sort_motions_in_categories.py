import threading
from typing import cast

from tests.system.action.base import BaseActionTestCase
from tests.system.action.lock import (
    OSTestThread,
    monkeypatch_datastore_adapter_write,
    pytest_thread_local,
)


class MotionCategorySortMotionsInCategoriesActionTest(BaseActionTestCase):
    def test_sort_correct_1(self) -> None:
        self.create_model("motion_category/222", {})
        self.create_model("motion/31", {"category_id": 222})
        self.create_model("motion/32", {"category_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.sort_motions_in_category",
                    "data": [{"id": 222, "motion_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model_31 = self.get_model("motion/31")
        assert model_31.get("category_weight") == 2
        model_32 = self.get_model("motion/32")
        assert model_32.get("category_weight") == 1

    def test_sort_missing_model(self) -> None:
        self.create_model("motion_category/222", {})
        self.create_model("motion/31", {"category_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.sort_motions_in_category",
                    "data": [{"id": 222, "motion_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Id 32 not in db_instances." in str(response.data)

    def test_sort_another_section_db(self) -> None:
        self.create_model("motion_category/222", {})
        self.create_model("motion/31", {"category_id": 222})
        self.create_model("motion/32", {"category_id": 222})
        self.create_model("motion/33", {"category_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.sort_motions_in_category",
                    "data": [{"id": 222, "motion_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Additional db_instances found." in str(response.data)

    def test_sort_extra_motion_race_condition(self) -> None:
        self.create_model("meeting/222", {"name": "meeting222"})
        self.create_model(
            "motion_workflow/12",
            {"name": "name_workflow1", "first_state_id": 34, "state_ids": [34]},
        )
        self.create_model(
            "motion_state/34", {"name": "name_state34", "meeting_id": 222}
        )
        self.create_model("motion_category/222", {"meeting_id": 222})
        self.create_model("motion/31", {"category_id": 222})
        self.create_model("motion/32", {"category_id": 222})

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
                target=thread_method_extra_motion,
                kwargs={
                    "test_instance": self,
                    "name": "Passing extra motion-Thread",
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
        self.assert_thread_exception(thread1, "Additional db_instances found")


def thread_method_sorting(
    test_instance: MotionCategorySortMotionsInCategoriesActionTest,
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
                "action": "motion_category.sort_motions_in_category",
                "data": [{"id": 222, "motion_ids": [32, 31]}],
            }
        ],
    )
    cast(OSTestThread, threading.current_thread()).check_response(response)


def thread_method_extra_motion(
    test_instance: MotionCategorySortMotionsInCategoriesActionTest,
    name: str,
) -> None:
    pytest_thread_local.name = name
    response = test_instance.client.post(
        "/",
        json=[
            {
                "action": "motion.create",
                "data": [
                    {
                        "title": "test_title",
                        "meeting_id": 222,
                        "category_id": 222,
                        "text": "test text",
                        "workflow_id": 12,
                    }
                ],
            }
        ],
    )
    cast(OSTestThread, threading.current_thread()).check_response(response)
