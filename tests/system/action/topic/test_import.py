from tests.system.action.base import BaseActionTestCase


class TopicJsonImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/22": {"name": "test", "is_active_in_organization_id": 1},
                "action_worker/2": {
                    "result": [
                        {
                            "status": "new",
                            "error": [],
                            "data": {"title": "test", "meeting_id": 22},
                        },
                        {
                            "status": "error",
                            "error": ["test"],
                            "data": {"title": "broken", "meeting_id": 22},
                        },
                    ]
                },
            }
        )

    def test_import_correct(self) -> None:
        response = self.request("topic.import", {"id": 2, "command": "import"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/1", {"title": "test", "meeting_id": 22})
        self.assert_model_exists("meeting/22", {"topic_ids": [1]})
        self.assert_model_exists("action_worker/2", {"result": None})

    def test_import_abort(self) -> None:
        response = self.request("topic.import", {"id": 2, "command": "abort"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("action_worker/2", {"result": None})

        response = self.request("topic.import", {"id": 2, "command": "abort"})
        self.assert_status_code(response, 400)
        assert "Topic import is aborted or done." in response.json["message"]
