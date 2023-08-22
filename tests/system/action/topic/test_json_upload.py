from time import time

from openslides_backend.action.mixins.import_mixins import ImportState
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class TopicJsonUpload(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/22": {"name": "test", "is_active_in_organization_id": 1},
            }
        )

    def test_json_upload_agenda_data(self) -> None:
        start_time = int(time())
        response = self.request(
            "topic.json_upload",
            {
                "meeting_id": 22,
                "data": [
                    {
                        "title": "test",
                        "agenda_comment": "testtesttest",
                        "agenda_type": "hidden",
                        "agenda_duration": "50",
                        "wrong": 15,
                    }
                ],
            },
        )
        end_time = int(time())
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "title": "test",
                "meeting_id": 22,
                "agenda_comment": "testtesttest",
                "agenda_type": "hidden",
                "agenda_duration": 50,
            },
        }
        worker = self.assert_model_exists(
            "action_worker/1", {"state": ImportState.DONE}
        )
        assert start_time <= worker.get("created", -1) <= end_time
        assert start_time <= worker.get("timestamp", -1) <= end_time

    def test_json_upload_empty_data(self) -> None:
        response = self.request(
            "topic.json_upload",
            {"meeting_id": 22, "data": []},
        )
        self.assert_status_code(response, 400)
        assert "data.data must contain at least 1 items" in response.json["message"]

    def test_json_upload_integer_parsing_error(self) -> None:
        response = self.request(
            "topic.json_upload",
            {
                "meeting_id": 22,
                "data": [
                    {
                        "title": "test",
                        "agenda_comment": "testtesttest",
                        "agenda_type": "hidden",
                        "agenda_duration": "X50",
                        "wrong": 15,
                    }
                ],
            },
        )
        self.assert_status_code(response, 400)
        assert "Could not parse X50 expect integer" in response.json["message"]

    def test_json_upload_results(self) -> None:
        response = self.request(
            "topic.json_upload",
            {"meeting_id": 22, "data": [{"title": "test"}]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "action_worker/1",
            {
                "result": {
                    "import": "topic",
                    "rows": [
                        {
                            "state": ImportState.NEW,
                            "messages": [],
                            "data": {"title": "test", "meeting_id": 22},
                        }
                    ],
                }
            },
        )
        result = response.json["results"][0][0]
        assert result == {
            "id": 1,
            "headers": [
                {"property": "title", "type": "string"},
                {"property": "text", "type": "string"},
                {"property": "agenda_comment", "type": "string"},
                {"property": "agenda_type", "type": "string"},
                {"property": "agenda_duration", "type": "integer"},
            ],
            "rows": [
                {
                    "state": ImportState.NEW,
                    "messages": [],
                    "data": {"title": "test", "meeting_id": 22},
                }
            ],
            "statistics": [
                {"name": "total", "value": 1},
                {"name": "created", "value": 1},
                {"name": "updated", "value": 0},
                {"name": "error", "value": 0},
                {"name": "warning", "value": 0},
            ],
            "state": ImportState.DONE,
        }

    def test_json_upload_duplicate_in_db(self) -> None:
        self.set_models(
            {
                "topic/3": {"title": "test", "meeting_id": 22},
                "meeting/22": {"topic_ids": [3]},
            }
        )
        response = self.request(
            "topic.json_upload",
            {"meeting_id": 22, "data": [{"title": "test"}]},
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["rows"] == [
            {
                "state": ImportState.WARNING,
                "messages": ["Duplicate"],
                "data": {"title": "test", "meeting_id": 22},
            }
        ]

    def test_json_upload_duplicate_in_data(self) -> None:
        response = self.request(
            "topic.json_upload",
            {
                "meeting_id": 22,
                "data": [{"title": "test"}, {"title": "bla"}, {"title": "test"}],
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["rows"][2]["messages"] == ["Duplicate"]
        assert result["rows"][2]["state"] == ImportState.WARNING
        self.assert_model_exists(
            "action_worker/1",
            {
                "result": {
                    "import": "topic",
                    "rows": [
                        {
                            "state": ImportState.NEW,
                            "messages": [],
                            "data": {"title": "test", "meeting_id": 22},
                        },
                        {
                            "state": ImportState.NEW,
                            "messages": [],
                            "data": {"title": "bla", "meeting_id": 22},
                        },
                        {
                            "state": ImportState.WARNING,
                            "messages": ["Duplicate"],
                            "data": {"title": "test", "meeting_id": 22},
                        },
                    ],
                }
            },
        )

    def test_json_upload_no_permission(self) -> None:
        self.base_permission_test(
            {}, "topic.json_upload", {"data": [{"title": "test"}], "meeting_id": 1}
        )

    def test_json_uplad_permission(self) -> None:
        self.base_permission_test(
            {},
            "topic.json_upload",
            {"data": [{"title": "test"}], "meeting_id": 1},
            Permissions.AgendaItem.CAN_MANAGE,
        )
