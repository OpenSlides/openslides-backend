import threading
from typing import cast

from tests.system.action.base import BaseActionTestCase
from tests.system.action.lock import (
    OSTestThread,
    monkeypatch_datastore_adapter_write,
    pytest_thread_local,
)


class AgendaItemSortActionTest(BaseActionTestCase):
    def test_sort_single_node_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("agenda_item/22", {"meeting_id": 222, "comment": "test1"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.sort",
                    "data": [{"meeting_id": 222, "tree": [{"id": 22}]}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        assert "Actions handled successfully" in str(response.data)
        model_22 = self.get_model("agenda_item/22")
        assert model_22.get("weight") == 2
        assert model_22.get("parent_id") is None
        assert model_22.get("child_ids") == []
        assert model_22.get("level") == 0

    def test_sort_not_all_sorted(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("agenda_item/22", {"meeting_id": 222, "comment": "test1"})
        self.create_model("agenda_item/23", {"meeting_id": 222, "comment": "test"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.sort",
                    "data": [{"meeting_id": 222, "tree": [{"id": 22}]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Did not recieve 2 ids, got 1" in str(response.data)

    def test_sort_complex_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("agenda_item/1", {"meeting_id": 222, "comment": "test_root"})
        self.create_model("agenda_item/11", {"meeting_id": 222, "comment": "test_1_1"})
        self.create_model("agenda_item/12", {"meeting_id": 222, "comment": "test_1_2"})
        self.create_model("agenda_item/21", {"meeting_id": 222, "comment": "test_2_1"})
        self.create_model("agenda_item/22", {"meeting_id": 222, "comment": "test_2_2"})
        self.create_model("agenda_item/23", {"meeting_id": 222, "comment": "test_2_3"})

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
            json=[{"action": "agenda_item.sort", "data": [valid_data]}],
        )
        self.assert_status_code(response, 200)
        fqids_in_preorder = [
            "agenda_item/1",
            "agenda_item/11",
            "agenda_item/21",
            "agenda_item/12",
            "agenda_item/22",
            "agenda_item/23",
        ]
        weight = 2
        for fqid in fqids_in_preorder:
            model = self.get_model(fqid)
            assert model.get("weight") == weight
            weight += 2
        assert self.get_model("agenda_item/1").get("level") == 0
        assert self.get_model("agenda_item/11").get("level") == 1
        assert self.get_model("agenda_item/12").get("level") == 1
        assert self.get_model("agenda_item/21").get("level") == 2
        assert self.get_model("agenda_item/22").get("level") == 2
        assert self.get_model("agenda_item/23").get("level") == 2

    def test_sort_not_a_tree(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("agenda_item/1", {"meeting_id": 222, "comment": "test_root"})
        self.create_model("agenda_item/11", {"meeting_id": 222, "comment": "test_1_1"})
        self.create_model("agenda_item/12", {"meeting_id": 222, "comment": "test_1_2"})

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
            json=[{"action": "agenda_item.sort", "data": [not_tree_data]}],
        )
        self.assert_status_code(response, 400)
        assert "Duplicate id in sort tree: 12" in str(response.data)

    def test_sort_circle_fail(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("agenda_item/1", {"meeting_id": 222, "comment": "test_root"})
        self.create_model("agenda_item/11", {"meeting_id": 222, "comment": "test_1_1"})
        self.create_model("agenda_item/12", {"meeting_id": 222, "comment": "test_1_2"})

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
            json=[{"action": "agenda_item.sort", "data": [circle_data]}],
        )
        self.assert_status_code(response, 400)
        assert "Duplicate id in sort tree: 1" in str(response.data)

    def test_small_tree_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model("agenda_item/1", {"meeting_id": 222, "comment": "test_root"})
        self.create_model("agenda_item/11", {"meeting_id": 222, "comment": "test_1_1"})
        self.create_model("agenda_item/12", {"meeting_id": 222, "comment": "test_1_2"})

        small_tree_data = {
            "meeting_id": 222,
            "tree": [{"id": 1, "children": [{"id": 11}, {"id": 12}]}],
        }
        response = self.client.post(
            "/",
            json=[{"action": "agenda_item.sort", "data": [small_tree_data]}],
        )
        self.assert_status_code(response, 200)
        model_1 = self.get_model("agenda_item/1")
        assert model_1.get("weight") == 2
        assert model_1.get("parent_id") is None
        assert model_1.get("child_ids") == [11, 12]
        assert model_1.get("level") == 0
        model_11 = self.get_model("agenda_item/11")
        assert model_11.get("weight") == 4
        assert model_11.get("parent_id") == 1
        assert model_11.get("child_ids") == []
        assert model_11.get("level") == 1
        model_12 = self.get_model("agenda_item/12")
        assert model_12.get("weight") == 6
        assert model_12.get("parent_id") == 1
        assert model_12.get("child_ids") == []
        assert model_12.get("level") == 1

    def test_tree_sort_delete_race_condition(self) -> None:
        self.create_model(
            "meeting/222", {"name": "meeting222", "agenda_item_ids": [1, 11, 12]}
        )
        self.create_model("agenda_item/1", {"meeting_id": 222, "comment": "test_root"})
        self.create_model("agenda_item/11", {"meeting_id": 222, "comment": "test_1_1"})
        self.create_model("agenda_item/12", {"meeting_id": 222, "comment": "test_1_2"})

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
                    "name": "Passing delete-item-Thread",
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
        self.assert_thread_exception(thread1, "Id in sort tree does not exist: 11")


def thread_method_sorting(
    test_instance: AgendaItemSortActionTest,
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
                "action": "agenda_item.sort",
                "data": [
                    {
                        "meeting_id": 222,
                        "tree": [{"id": 1, "children": [{"id": 11}, {"id": 12}]}],
                    }
                ],
            }
        ],
    )

    cast(OSTestThread, threading.current_thread()).check_response(response)


def thread_method_delete(
    test_instance: AgendaItemSortActionTest,
    name: str,
) -> None:
    pytest_thread_local.name = name
    response = test_instance.client.post(
        "/",
        json=[
            {
                "action": "agenda_item.delete",
                "data": [{"id": 11}],
            }
        ],
    )
    cast(OSTestThread, threading.current_thread()).check_response(response)
