from time import time

from openslides_backend.action.actions.topic.json_upload import ImportStatus
from tests.system.action.base import BaseActionTestCase


class TopicJsonImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/22": {"name": "test", "is_active_in_organization_id": 1},
                "action_worker/2": {
                    "result": {
                        "import": "topic",
                        "rows": [
                            {
                                "status": ImportStatus.NEW,
                                "error": [],
                                "data": {"title": "test", "meeting_id": 22},
                            },
                            {
                                "status": ImportStatus.ERROR,
                                "error": ["test"],
                                "data": {"title": "broken", "meeting_id": 22},
                            },
                        ],
                    }
                },
            }
        )

    def test_import_correct(self) -> None:
        start_time = int(time())
        response = self.request("topic.import", {"id": 2})
        end_time = int(time())
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/1", {"title": "test", "meeting_id": 22})
        self.assert_model_exists("meeting/22", {"topic_ids": [1]})
        worker = self.assert_model_exists("action_worker/2", {"state": "end"})
        assert start_time <= worker.get("timestamp", -1) <= end_time

    def test_import_duplicates_in_db(self) -> None:
        self.set_models(
            {
                "topic/1": {"title": "test", "meeting_id": 22},
                "meeting/22": {"topic_ids": [1]},
            }
        )
        response = self.request("topic.import", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("topic/2")
