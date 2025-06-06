from openslides_backend.action.mixins.import_mixins import ImportState
from tests.system.action.base import BaseActionTestCase
from tests.system.action.topic.test_json_upload import TopicJsonUploadForUseInImport


class TopicJsonImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/22": {"name": "test", "is_active_in_organization_id": 1},
                "import_preview/2": {
                    "state": ImportState.DONE,
                    "name": "topic",
                    "result": {
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "title": {"value": "test", "info": ImportState.NEW},
                                    "meeting_id": 22,
                                },
                            },
                        ],
                    },
                },
            }
        )

    def test_import_correct(self) -> None:
        response = self.request("topic.import", {"id": 2, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/1", {"title": "test", "meeting_id": 22})
        self.assert_model_exists("meeting/22", {"topic_ids": [1]})
        self.assert_model_not_exists("import_preview/2")

    def test_import_abort_with_import_false(self) -> None:
        response = self.request("topic.import", {"id": 2, "import": False})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("topic/1")
        self.assert_model_not_exists("import_preview/2")

    def test_import_abort_with_import_false_but_wrong_type(self) -> None:
        self.set_models({"import_preview/2": {"name": "account"}})
        response = self.request("topic.import", {"id": 2, "import": False})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("topic/1")
        self.assert_model_exists("import_preview/2")  # may not delete "account" preview

    def test_import_abort_import_with_error(self) -> None:
        self.set_models(
            {
                "import_preview/2": {
                    "state": ImportState.ERROR,
                },
            }
        )
        response = self.request("topic.import", {"id": 2, "import": True})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Error in import. Data will not be imported.", response.json["message"]
        )
        self.assert_model_not_exists("topic/1")
        self.assert_model_exists("import_preview/2")

    def test_import_found_id_and_text_field(self) -> None:
        self.set_models(
            {
                "topic/1": {"title": "test", "meeting_id": 22},
                "meeting/22": {"topic_ids": [1]},
                "import_preview/2": {
                    "state": ImportState.DONE,
                    "result": {
                        "import": "topic",
                        "rows": [
                            {
                                "state": ImportState.DONE,
                                "messages": ["Existing topic will be updated."],
                                "data": {
                                    "title": {
                                        "value": "test",
                                        "info": ImportState.WARNING,
                                        "id": 1,
                                    },
                                    "id": 1,
                                    "meeting_id": 22,
                                    "text": "this should be updated",
                                },
                            },
                        ],
                    },
                },
            }
        )
        response = self.request("topic.import", {"id": 2, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "topic/1",
            {"title": "test", "meeting_id": 22, "text": "this should be updated"},
        )

    def test_import_found_id_and_agenda_fields(self) -> None:
        self.set_models(
            {
                "topic/1": {"title": "test", "meeting_id": 22, "agenda_item_id": 7},
                "agenda_item/7": {
                    "content_object_id": "topic/1",
                    "meeting_id": 22,
                    "duration": 20,
                },
                "meeting/22": {"topic_ids": [1]},
                "import_preview/2": {
                    "state": ImportState.DONE,
                    "result": {
                        "import": "topic",
                        "rows": [
                            {
                                "state": ImportState.DONE,
                                "messages": ["Existing topic will be updated."],
                                "data": {
                                    "title": {
                                        "value": "test",
                                        "info": ImportState.WARNING,
                                        "id": 1,
                                    },
                                    "id": 1,
                                    "meeting_id": 22,
                                    "agenda_comment": "test",
                                    "agenda_type": "hidden",
                                    "agenda_duration": 40,
                                },
                            },
                        ],
                    },
                },
            }
        )
        response = self.request("topic.import", {"id": 2, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "topic/1",
            {"title": "test", "meeting_id": 22, "agenda_item_id": 7},
        )
        self.assert_model_exists(
            "agenda_item/7",
            {
                "content_object_id": "topic/1",
                "comment": "test",
                "type": "hidden",
                "duration": 40,
            },
        )

    def test_import_duplicate_and_topic_deleted(self) -> None:
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
        self.assert_model_exists("import_preview/3")
        response = self.request("topic.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("topic/1")
        response = self.request("topic.import", {"id": 3, "import": True})
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["rows"][0] == {
            "state": ImportState.ERROR,
            "messages": [
                "Existing topic will be updated.",
                "Error: topic 1 not found anymore for updating topic 'test'.",
            ],
            "data": {
                "id": 1,
                "title": {"id": 1, "info": "error", "value": "test"},
                "meeting_id": 22,
            },
        }
        self.assert_model_not_exists("topic/2")


class TopicImportWithIncludedJsonUpload(TopicJsonUploadForUseInImport):
    def test_import_agenda_data(self) -> None:
        self.json_upload_agenda_data()
        response = self.request("topic.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists("topic/1", {"title": "test"})
        self.assert_model_exists(
            "agenda_item/1",
            {"comment": "testtesttest", "type": "hidden", "duration": 50},
        )

    def test_import_duplicate_in_db(self) -> None:
        self.json_upload_duplicate_in_db()
        response = self.request("topic.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.DONE
        self.assert_model_exists(
            "topic/3", {"title": "test", "text": "new one", "meeting_id": 22}
        )
        self.assert_model_not_exists("topic/4")

    def test_import_done_switched_to_new(self) -> None:
        self.json_upload_duplicate_in_db()
        self.request("topic.delete", {"id": 3})
        self.assert_model_not_exists("topic/3")
        response = self.request("topic.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.ERROR
        assert result["rows"][0]["messages"] == [
            "Existing topic will be updated.",
            "Error: topic 3 not found anymore for updating topic 'test'.",
        ]

    def test_import_topic_switched_id(self) -> None:
        self.json_upload_duplicate_in_db()
        self.request("topic.delete", {"id": 3})
        self.assert_model_not_exists("topic/3")
        self.create_model("topic/4", {"title": "test", "meeting_id": 22})
        response = self.request("topic.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.ERROR
        assert result["rows"][0]["messages"] == [
            "Existing topic will be updated.",
            "Error: topic 'test' found in different id (4 instead of 3)",
        ]

    def test_import_topic_duplicate_id(self) -> None:
        self.json_upload_duplicate_in_db()
        self.create_model("topic/4", {"title": "test", "meeting_id": 22})
        response = self.request("topic.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.ERROR
        assert result["rows"][0]["messages"] == [
            "Existing topic will be updated.",
            "Error: topic 'test' is duplicated in import.",
        ]
