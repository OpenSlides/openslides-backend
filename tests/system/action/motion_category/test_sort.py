import threading
from typing import cast

from tests.system.action.base import BaseActionTestCase
from tests.system.action.lock import (
    OSTestThread,
    monkeypatch_datastore_adapter_write,
    pytest_thread_local,
)


class MotionCategorySortActionTest(BaseActionTestCase):
    def test_sort_singe_node_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("motion_category/22", {"meeting_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.sort",
                    "data": [{"meeting_id": 222, "tree": [{"id": 22}]}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        assert "Actions handled successfully" in str(response.data)
        model_22 = self.get_model("motion_category/22")
        assert model_22.get("weight") == 2
        assert model_22.get("parent_id") is None
        assert model_22.get("child_ids") == []
        assert model_22.get("level") == 0

    def test_sort_not_all_sorted(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("motion_category/22", {"meeting_id": 222})
        self.create_model("motion_category/23", {"meeting_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.sort",
                    "data": [{"meeting_id": 222, "tree": [{"id": 22}]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Did not recieve 2 ids, got 1" in str(response.data)

    def test_sort_complex_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("motion_category/1", {"meeting_id": 222})
        self.create_model("motion_category/11", {"meeting_id": 222})
        self.create_model("motion_category/12", {"meeting_id": 222})
        self.create_model("motion_category/21", {"meeting_id": 222})
        self.create_model("motion_category/22", {"meeting_id": 222})
        self.create_model("motion_category/23", {"meeting_id": 222})

        valid_data = {
            "meeting_id": 222,
            "tree": [
                {
                    "id": 1,
                    "children": [
                        {"id": 11, "children": [{"id": 21}]},
                        {"id": 12, "children": [{"id": 22}, {"id": 23}]},
                    ],
                }
            ],
        }

        response = self.client.post(
            "/",
            json=[{"action": "motion_category.sort", "data": [valid_data]}],
        )
        self.assert_status_code(response, 200)
        fqids_in_preorder = [
            "motion_category/1",
            "motion_category/11",
            "motion_category/21",
            "motion_category/12",
            "motion_category/22",
            "motion_category/23",
        ]
        weight = 2
        for fqid in fqids_in_preorder:
            model = self.get_model(fqid)
            assert model.get("weight") == weight
            weight += 2
        assert self.get_model("motion_category/1").get("level") == 0
        assert self.get_model("motion_category/11").get("level") == 1
        assert self.get_model("motion_category/12").get("level") == 1
        assert self.get_model("motion_category/21").get("level") == 2
        assert self.get_model("motion_category/22").get("level") == 2
        assert self.get_model("motion_category/23").get("level") == 2

    def test_sort_not_a_tree(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("motion_category/1", {"meeting_id": 222})
        self.create_model("motion_category/11", {"meeting_id": 222})
        self.create_model("motion_category/12", {"meeting_id": 222})

        not_tree_data = {
            "meeting_id": 222,
            "tree": [
                {
                    "id": 1,
                    "children": [{"id": 11, "children": [{"id": 12}]}, {"id": 12}],
                }
            ],
        }
        response = self.client.post(
            "/",
            json=[{"action": "motion_category.sort", "data": [not_tree_data]}],
        )
        self.assert_status_code(response, 400)
        assert "Duplicate id in sort tree: 12" in str(response.data)

    def test_sort_circle_fail(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("motion_category/1", {"meeting_id": 222})
        self.create_model("motion_category/11", {"meeting_id": 222})
        self.create_model("motion_category/12", {"meeting_id": 222})

        circle_data = {
            "meeting_id": 222,
            "tree": [
                {
                    "id": 1,
                    "children": [
                        {"id": 11, "children": [{"id": 12, "children": [{"id": 1}]}]}
                    ],
                }
            ],
        }
        response = self.client.post(
            "/",
            json=[{"action": "motion_category.sort", "data": [circle_data]}],
        )
        self.assert_status_code(response, 400)
        assert "Duplicate id in sort tree: 1" in str(response.data)

    def test_small_tree_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("motion_category/1", {"meeting_id": 222})
        self.create_model("motion_category/11", {"meeting_id": 222})
        self.create_model("motion_category/12", {"meeting_id": 222})

        small_tree_data = {
            "meeting_id": 222,
            "tree": [{"id": 1, "children": [{"id": 11}, {"id": 12}]}],
        }
        response = self.client.post(
            "/",
            json=[{"action": "motion_category.sort", "data": [small_tree_data]}],
        )
        self.assert_status_code(response, 200)
        model_1 = self.get_model("motion_category/1")
        assert model_1.get("weight") == 2
        assert model_1.get("parent_id") is None
        assert model_1.get("child_ids") == [11, 12]
        assert model_1.get("level") == 0
        model_11 = self.get_model("motion_category/11")
        assert model_11.get("weight") == 4
        assert model_11.get("parent_id") == 1
        assert model_11.get("child_ids") == []
        assert model_11.get("level") == 1
        model_12 = self.get_model("motion_category/12")
        assert model_12.get("weight") == 6
        assert model_12.get("parent_id") == 1
        assert model_12.get("child_ids") == []
        assert model_12.get("level") == 1

    def test_with_deleted_model(self) -> None:
        self.create_model("meeting/222", {"motion_category_ids": [2, 3]})
        self.create_model("motion_category/1", {"meeting_id": 222}, deleted=True)
        self.create_model("motion_category/2", {"meeting_id": 222})
        self.create_model("motion_category/3", {"meeting_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.sort",
                    "data": [{"meeting_id": 222, "tree": [{"id": 2}, {"id": 3}]}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        assert "Actions handled successfully" in str(response.data)
        category_1 = self.get_model("motion_category/1")
        assert category_1.get("weight") is None
        category_2 = self.get_model("motion_category/2")
        assert category_2.get("weight") == 2
        category_3 = self.get_model("motion_category/3")
        assert category_3.get("weight") == 4

    def test_sort_single_node_race_condition(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("motion_category/22", {"meeting_id": 222})

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
                target=thread_method_extra_category,
                kwargs={
                    "test_instance": self,
                    "name": "Passing extra category-Thread",
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
        self.assert_thread_exception(thread1, "Did not recieve 2 ids, got 1")


def thread_method_sorting(
    test_instance: MotionCategorySortActionTest,
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
                "action": "motion_category.sort",
                "data": [{"meeting_id": 222, "tree": [{"id": 22}]}],
            }
        ],
    )

    cast(OSTestThread, threading.current_thread()).check_response(response)


def thread_method_extra_category(
    test_instance: MotionCategorySortActionTest,
    name: str,
) -> None:
    pytest_thread_local.name = name
    response = test_instance.client.post(
        "/",
        json=[
            {
                "action": "motion_category.create",
                "data": [
                    {
                        "name": "test_Xcdfgee",
                        "prefix": "prefix_niqCxoXA",
                        "meeting_id": 222,
                    }
                ],
            }
        ],
    )
    cast(OSTestThread, threading.current_thread()).check_response(response)
