from datetime import datetime
from threading import Lock, Thread
from time import sleep
from typing import Any

import pytest

from openslides_backend.action.action_worker import ActionWorkerState
from openslides_backend.shared.interfaces.event import Event, EventType
from openslides_backend.shared.interfaces.write_request import WriteRequest
from openslides_backend.shared.patterns import fqid_from_collection_and_id
from tests.system.action.base import BaseActionTestCase


class ActionWorkerTest(BaseActionTestCase):
    start1: datetime
    end1: datetime

    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_workflow_timestamp": True,
                },
            }
        )

    def test_action_worker_ready_before_timeout_okay(self) -> None:
        """action thread used, but ended in time"""
        response = self.request(
            "motion.create",
            {
                "title": "test_title",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test_text",
            },
        )
        self.assert_status_code(response, 200)
        assert self.get_thread_by_name("action_worker") is None
        self.assert_model_exists("motion/1", {"title": "test_title"})
        self.assert_model_not_exists("action_worker/1")

    def test_action_worker_ready_before_timeout_exception(self) -> None:
        """action thread used, but ended in time with exception"""
        response = self.request(
            "motion.create",
            {
                "title": "test_title",
                "meeting_id": 222,
                "workflow_id": 12,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn("Text is required", response.json["message"])
        assert self.get_thread_by_name("action_worker") is None
        self.assert_model_not_exists("motion/1")
        self.assert_model_not_exists("action_worker/1")

    def test_action_worker_not_ready_before_timeout_okay(self) -> None:
        """action thread used, main process ends before action_worker is ready,
        but the final result will be okay.
        """
        self.set_thread_watch_timeout(0)
        count_motions: int = 2
        response = self.request_multi(
            "motion.create",
            [
                {
                    "title": f"test_title {i+1}",
                    "meeting_id": 222,
                    "workflow_id": 12,
                    "text": "test_text",
                }
                for i in range(count_motions)
            ],
        )

        self.assert_status_code(response, 202)
        self.assertIn(
            "Action (motion.create) lasts too long. action_worker/1 written to database. Get the result from database, when the job is done.",
            response.json["message"],
        )
        self.assertFalse(
            response.json["success"],
            "Action worker still not finished, success must be False.",
        )
        self.assertEqual(
            response.json["results"][0][0],
            {"fqid": "action_worker/1", "name": "motion.create", "written": True},
        )
        if action_worker := self.get_thread_by_name("action_worker"):
            action_worker.join()
        self.assert_model_exists("motion/1", {"title": "test_title 1"})
        self.assert_model_exists(
            f"motion/{count_motions}", {"title": f"test_title {count_motions}"}
        )
        self.assert_model_exists(
            "action_worker/1", {"state": ActionWorkerState.END, "user_id": 1}
        )

    def test_internal_action_worker_not_ready_before_timeout_okay(self) -> None:
        """action thread used, main process ends before action_worker is ready,
        but the final result will be okay.
        """
        self.create_meeting(222)
        self.set_user_groups(1, [222])
        chat_message_ids = [i + 1 for i in range(50)]
        self.set_models(
            {
                "meeting/222": {
                    "chat_group_ids": [22],
                    "chat_message_ids": chat_message_ids,
                },
                "meeting_user/1": {"chat_message_ids": chat_message_ids},
                "chat_group/22": {
                    "name": "blob",
                    "chat_message_ids": chat_message_ids,
                    "read_group_ids": [222, 223, 224],
                    "write_group_ids": [222],
                    "meeting_id": 222,
                },
                **{
                    fqid_from_collection_and_id("chat_message", id_): {
                        "content": f"Message {id_}",
                        "created": 1600000000 + id_,
                        "meeting_user_id": 1,
                        "chat_group_id": 22,
                        "meeting_id": 222,
                    }
                    for id_ in chat_message_ids
                },
            }
        )
        self.set_thread_watch_timeout(0)
        response = self.request("chat_group.clear", {"id": 22}, internal=True)

        self.assert_status_code(response, 202)
        self.assertIn(
            "Action (chat_group.clear) lasts too long. action_worker/1 written to database. Get the result from database, when the job is done.",
            response.json["message"],
        )
        self.assertFalse(
            response.json["success"],
            "Action worker still not finished, success must be False.",
        )
        self.assertEqual(
            response.json["results"][0][0],
            {"fqid": "action_worker/1", "name": "chat_group.clear", "written": True},
        )
        if action_worker := self.get_thread_by_name("action_worker"):
            action_worker.join()
        self.assert_model_exists("chat_group/22", {"chat_message_ids": []})
        for id_ in chat_message_ids:
            self.assert_model_deleted(fqid_from_collection_and_id("chat_message", id_))
        self.assert_model_exists(
            "action_worker/1", {"state": ActionWorkerState.END, "user_id": -1}
        )

    def test_action_worker_not_ready_before_timeout_exception(self) -> None:
        """action thread used, ended after timeout"""
        self.set_thread_watch_timeout(0)
        count_motions: int = 2
        data: list[dict[str, Any]] = [
            {
                "title": f"test_title {i+1}",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test_text",
            }
            for i in range(count_motions)
        ]
        data.append(
            {
                "title": f"test_title {count_motions+1}",
                "meeting_id": 222,
                "workflow_id": 12,
            }
        )

        response = self.request_multi("motion.create", data)

        self.assert_status_code(response, 202)
        self.assertIn(
            "Action (motion.create) lasts too long. action_worker/1 written to database. Get the result from database, when the job is done.",
            response.json["message"],
        )
        self.assertFalse(
            response.json["success"],
            "Action worker still not finished, success must be False.",
        )
        self.assertEqual(
            response.json["results"][0][0],
            {"fqid": "action_worker/1", "name": "motion.create", "written": True},
        )
        self.assert_model_exists("action_worker/1")
        if action_worker := self.get_thread_by_name("action_worker"):
            action_worker.join()
        self.assert_model_not_exists("motion/1")
        action_worker1 = self.assert_model_exists(
            "action_worker/1", {"state": ActionWorkerState.END, "user_id": 1}
        )
        self.assertFalse(action_worker1["result"]["success"])
        self.assertIn("Text is required", action_worker1["result"]["message"])

    def test_action_error_index_with_action_worker(self) -> None:
        self.set_thread_watch_timeout(0)
        response = self.request_multi(
            "user.create",
            [
                {
                    "username": "test",
                },
                {
                    "username": "admin",
                },
            ],
        )
        self.assert_status_code(response, 202)
        if action_worker := self.get_thread_by_name("action_worker"):
            action_worker.join()
        result = self.get_model("action_worker/1")["result"]
        expected = {"success": False, "action_data_error_index": 1}
        self.assertLessEqual(expected.items(), result.items())

    @pytest.mark.skip("Just for manual stress and thread tests")
    def test_action_worker_permanent_stress(self) -> None:
        self.lock = Lock()
        self.result_list: list[tuple] = []
        self.number = 201
        self.collection_types: dict[str, dict[str, str]] = {
            "motion_block": {},
            "topic": {},
            "assignment": {},
        }

        def thread_method(self: ActionWorkerTest, collection: str) -> None:
            for i in range(1, self.number):
                data = {
                    "title": f"title{i}",
                    "meeting_id": 222,
                    **self.collection_types[collection],
                }
                response = self.request(f"{collection}.create", data)
                with self.lock:
                    if response.status_code != 200:
                        self.result_list.append(
                            (
                                f"{collection}/{i}",
                                response.status_code,
                                response.json["message"],
                            )
                        )

        start = datetime.now()
        threads = []
        for collection in self.collection_types:
            thread = Thread(
                target=thread_method,
                args=(
                    self,
                    collection,
                ),
            )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
        print(f"Runtime: {datetime.now() - start}")
        assert not self.result_list

    def test_action_worker_create_action_worker_during_running_db_action(self) -> None:
        self.user_id = 1
        self.lock = Lock()
        self.number = 100

        def thread_method(self: ActionWorkerTest) -> None:
            with self.lock:
                data = [
                    {"prefix": f"boo{i}", "name": f"foo{i}", "meeting_id": 222}
                    for i in range(1, self.number)
                ]
                self.start1 = datetime.now()
            self.request_multi("motion_category.create", data)
            self.end1 = datetime.now()

        thread = Thread(target=thread_method, args=(self,))
        thread.start()
        sleep(0.1)

        with self.lock:
            start2 = datetime.now()
            self.new_id = self.datastore.reserve_id("action_worker")
            self.fqid = fqid_from_collection_and_id("action_worker", self.new_id)
            self.datastore.write(
                WriteRequest(
                    events=[
                        Event(
                            type=EventType.Create,
                            fqid=self.fqid,
                            fields={
                                "id": self.new_id,
                                "name": "test",
                                "state": ActionWorkerState.RUNNING,
                                "user_id": 1,
                            },
                        )
                    ],
                    user_id=self.user_id,
                    locked_fields={},
                )
            )
            end2 = datetime.now()
        thread.join()
        self.assert_model_exists(
            "action_worker/1",
            {"name": "test", "state": ActionWorkerState.RUNNING, "user_id": 1},
        )
        assert (
            self.start1 < start2 and self.end1 > end2
        ), "action_worker.create run outside of thread requests time intervall"

    def test_action_worker_delete_by_ids(self) -> None:
        self.user_id = 1
        new_ids = self.datastore.reserve_ids("action_worker", amount=3)
        for new_id in new_ids:
            self.datastore.write(
                WriteRequest(
                    events=[
                        Event(
                            type=EventType.Create,
                            fqid=fqid_from_collection_and_id("action_worker", new_id),
                            fields={
                                "id": new_id,
                                "name": "test",
                                "state": ActionWorkerState.RUNNING,
                                "user_id": 1,
                            },
                        )
                    ],
                    user_id=self.user_id,
                    locked_fields={},
                )
            )
            self.assert_model_exists(
                f"action_worker/{new_id}",
                {"name": "test", "state": ActionWorkerState.RUNNING, "user_id": 1},
            )

        self.datastore.write(
            WriteRequest(
                events=[
                    Event(type=EventType.Delete, fqid=f"action_worker/{new_id}")
                    for new_id in new_ids
                ],
                user_id=self.user_id,
                locked_fields={},
            )
        )
        for new_id in new_ids:
            self.assert_model_not_exists(f"action_worker/{new_id}")
