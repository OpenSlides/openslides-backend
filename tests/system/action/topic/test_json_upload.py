from tests.system.action.base import BaseActionTestCase


class TopicJsonUpload(BaseActionTestCase):
    def test_json_upload(self) -> None:
        self.set_models(
            {
                "meeting/22": {"name": "test", "is_active_in_organization_id": 1},
            }
        )
        response = self.request(
            "topic.json_upload",
            {"meeting_id": 22, "data": [{"meeting_id": 22, "title": "test"}]},
        )
        self.assert_status_code(response, 200)
