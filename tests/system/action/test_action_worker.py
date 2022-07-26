from typing import Any, Dict, List

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
        The THREAD_WATCH_TIMEOUT is fixed with 1 sec., if the result here is 200,
        increase the count_motions to fail.
        """
        count_motions: int = 100
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
            "Action lasts to long. Get the result from database, when the job is done.",
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
        if watcher_thread := self.get_thread_by_name("watcher_thread"):
            watcher_thread.join()
        self.assert_model_exists("action_worker/1", {"state": "end"})

    def test_action_worker_not_ready_before_timeout_exception(self) -> None:
        """action thread used, ended after timeout
        The THREAD_WATCH_TIMEOUT is fixed with 1 sec.,
        if the result status code here is 200,
        increase the count_motions to fail.
        """
        count_motions: int = 100
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
            "Action lasts to long. Get the result from database, when the job is done.",
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
        if watcher_thread := self.get_thread_by_name("watcher_thread"):
            watcher_thread.join()
        self.assert_model_not_exists("motion/1")
        action_worker1 = self.assert_model_exists("action_worker/1", {"state": "end"})
        self.assertFalse(action_worker1["result"]["success"])
        self.assertIn("Text is required", action_worker1["result"]["message"])
