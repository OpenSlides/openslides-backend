from datetime import datetime
from threading import Lock, Thread
from typing import Any, Dict, List, Tuple

import pytest

from tests.system.action.base import BaseActionTestCase


class ActionWorkerTest(BaseActionTestCase):
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
                    "set_created_timestamp": True,
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
        """action thread used, but ended in time with exeception"""
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
        self.set_thread_watch_timeout(0.0001)
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
            "Action lasts too long. action_worker/1 written to database. Get the result from database, when the job is done.",
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
        self.assert_model_exists("action_worker/1", {"state": "end"})

    def test_action_worker_not_ready_before_timeout_exception(self) -> None:
        """action thread used, ended after timeout"""
        self.set_thread_watch_timeout(0.0001)
        count_motions: int = 2
        data: List[Dict[str, Any]] = [
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
            "Action lasts too long. action_worker/1 written to database. Get the result from database, when the job is done.",
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
        action_worker1 = self.assert_model_exists("action_worker/1", {"state": "end"})
        self.assertFalse(action_worker1["result"]["success"])
        self.assertIn("Text is required", action_worker1["result"]["message"])

    @pytest.mark.skip("Just for manual stress and thread tests")
    def test_action_worker_permanent_stress(self) -> None:
        self.lock = Lock()
        self.result_list: List[Tuple] = []
        self.number = 201
        self.collection_types: Dict[str, Dict[str, str]] = {
            "motion_block": {},
            "topic": {},
            "assignment": {},
            "motion_statute_paragraph": {"text": "text"},
        }

        start = datetime.now()
        threads = []
        for collection in self.collection_types:
            thread = Thread(target=self.thread_method, args=(collection,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
        print(f"Runtime: {datetime.now() - start}")
        assert not self.result_list

    def thread_method(self, collection: str) -> None:
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
