from openslides_backend.action.mixins.import_mixins import ImportState
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
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {"title": "test", "meeting_id": 22},
                            },
                            {
                                "state": ImportState.ERROR,
                                "messages": ["test"],
                                "data": {"title": "broken", "meeting_id": 22},
                            },
                        ],
                    }
                },
            }
        )

    def test_import_correct(self) -> None:
        response = self.request("topic.import", {"id": 2, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/1", {"title": "test", "meeting_id": 22})
        self.assert_model_exists("meeting/22", {"topic_ids": [1]})
        self.assert_model_not_exists("action_worker/2")

    def test_import_abort(self) -> None:
        response = self.request("topic.import", {"id": 2, "import": False})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("topic/1")
        self.assert_model_not_exists("action_worker/2")

    def test_import_duplicate_in_db(self) -> None:
        self.set_models(
            {
                "topic/1": {"title": "test", "meeting_id": 22},
                "meeting/22": {"topic_ids": [1]},
            }
        )
        response = self.request("topic.import", {"id": 2, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("topic/2")

    def test_import_duplicate_and_topic_deleted_so_imported(self) -> None:
        self.set_models(
            {
                "topic/1": {"title": "test", "meeting_id": 22},
                "meeting/22": {"topic_ids": [1]},
            }
        )
        response = self.request(
            "topic.json_upload",
            {
                "meeting_id": 22,
                "data": [
                    {
                        "title": "test",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("action_worker/3")
        response = self.request("topic.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("topic/1")
        response = self.request("topic.import", {"id": 3, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/2", {"title": "test"})

    def test_import_duplicate_so_not_imported(self) -> None:
        self.set_models(
            {
                "topic/1": {"title": "test", "meeting_id": 22},
                "meeting/22": {"topic_ids": [1]},
            }
        )
        response = self.request(
            "topic.json_upload",
            {
                "meeting_id": 22,
                "data": [
                    {
                        "title": "test",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("action_worker/3")
        response = self.request("topic.import", {"id": 3, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("topic/2")

    def test_import_with_upload(self) -> None:
        response = self.request(
            "topic.json_upload",
            {
                "meeting_id": 22,
                "data": [
                    {
                        "title": "another title",
                    }
                ],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("action_worker/3")
        response = self.request("topic.import", {"id": 3, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "topic/1", {"title": "another title", "meeting_id": 22}
        )
        self.assert_model_exists("meeting/22", {"topic_ids": [1]})
        self.assert_model_not_exists("action_worker/3")
