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
            "import_preview/1",
            {
                "name": "topic",
                "state": ImportState.DONE,
                "result": {
                    "rows": [
                        {
                            "state": ImportState.NEW,
                            "messages": [],
                            "data": {
                                "title": {"value": "test", "info": ImportState.NEW},
                                "meeting_id": 22,
                            },
                        }
                    ],
                },
            },
        )
        result = response.json["results"][0][0]
        assert result == {
            "id": 1,
            "headers": [
                {"property": "title", "type": "string", "is_object": True},
                {"property": "text", "type": "string"},
                {"property": "agenda_comment", "type": "string"},
                {"property": "agenda_type", "type": "string"},
                {"property": "agenda_duration", "type": "integer"},
            ],
            "rows": [
                {
                    "state": ImportState.NEW,
                    "messages": [],
                    "data": {
                        "title": {"value": "test", "info": ImportState.NEW},
                        "meeting_id": 22,
                    },
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
        assert result["state"] == ImportState.ERROR
        assert result["rows"][0]["state"] == ImportState.ERROR
        assert result["rows"][1]["state"] == ImportState.NEW
        assert result["rows"][2]["state"] == ImportState.ERROR
        self.assert_model_exists(
            "import_preview/1",
            {
                "name": "topic",
                "state": "error",
                "result": {
                    "rows": [
                        {
                            "state": ImportState.ERROR,
                            "messages": ["Duplicated topic name 'test'."],
                            "data": {
                                "title": {"value": "test", "info": ImportState.ERROR},
                                "meeting_id": 22,
                            },
                        },
                        {
                            "state": ImportState.NEW,
                            "messages": [],
                            "data": {
                                "title": {"value": "bla", "info": ImportState.NEW},
                                "meeting_id": 22,
                            },
                        },
                        {
                            "state": ImportState.ERROR,
                            "messages": ["Duplicated topic name 'test'."],
                            "data": {
                                "title": {"value": "test", "info": ImportState.ERROR},
                                "meeting_id": 22,
                            },
                        },
                    ],
                },
            },
        )

    def test_json_upload_duplicate_in_existing_topic(self) -> None:
        self.set_models({"topic/10": {"title": "test"}})
        response = self.request(
            "topic.json_upload",
            {
                "meeting_id": 22,
                "data": [{"title": "test"}, {"title": "test"}],
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.ERROR
        assert result["rows"][0]["state"] == ImportState.ERROR
        assert result["rows"][0]["messages"] == ["Duplicated topic name 'test'."]
        assert result["rows"][1]["state"] == ImportState.ERROR
        assert result["rows"][1]["messages"] == ["Duplicated topic name 'test'."]

    def test_json_upload_no_permission(self) -> None:
        self.base_permission_test(
            {}, "topic.json_upload", {"data": [{"title": "test"}], "meeting_id": 1}
        )

    def test_json_upload_permission(self) -> None:
        self.base_permission_test(
            {},
            "topic.json_upload",
            {"data": [{"title": "test"}], "meeting_id": 1},
            Permissions.AgendaItem.CAN_MANAGE,
        )

    def test_json_upload_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "topic.json_upload",
            {"data": [{"title": "test"}], "meeting_id": 1},
        )


class TopicJsonUploadForUseInImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/22": {"name": "test", "is_active_in_organization_id": 1},
            }
        )

    def json_upload_agenda_data(self) -> None:
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
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.DONE
        assert result["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "title": {"value": "test", "info": ImportState.NEW},
                "meeting_id": 22,
                "agenda_comment": "testtesttest",
                "agenda_type": "hidden",
                "agenda_duration": 50,
            },
        }
        worker = self.assert_model_exists(
            "import_preview/1", {"state": ImportState.DONE}
        )
        assert start_time <= worker.get("created", -1) <= end_time

    def json_upload_duplicate_in_db(self) -> None:
        self.set_models(
            {
                "topic/3": {"title": "test", "text": "old one", "meeting_id": 22},
                "meeting/22": {"topic_ids": [3]},
            }
        )
        response = self.request(
            "topic.json_upload",
            {"meeting_id": 22, "data": [{"title": "test", "text": "new one"}]},
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.WARNING
        assert result["rows"] == [
            {
                "state": ImportState.DONE,
                "messages": ["Existing topic will be updated."],
                "data": {
                    "id": 3,
                    "title": {"value": "test", "info": ImportState.WARNING, "id": 3},
                    "text": "new one",
                    "meeting_id": 22,
                },
            }
        ]
