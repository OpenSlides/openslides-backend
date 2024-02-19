from openslides_backend.action.mixins.import_mixins import ImportState
from tests.system.action.base import BaseActionTestCase


class BaseMotionJsonUpload(BaseActionTestCase):
    def setup_meeting_with_settings(
        self,
        id_: int = 42,
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> None:
        self.create_meeting(id_)
        self.create_user(f"user{id_}", [id_], None)
        self.set_models(
            {
                f"meeting/{id_}": {
                    "motions_reason_required": is_reason_required,
                    "motions_number_type": "per_category",
                    "motions_number_min_digits": 2,
                    "motion_ids": [id_, id_ * 100],
                    "motion_category_ids": [id_, id_ * 10, id_ * 100, id_ * 1000],
                },
                f"motion_state/{id_}": {"set_number": is_set_number},
                f"motion/{id_}": {
                    "title": "A",
                    "text": "<p>nice little</p>",
                    "reason": "motion",
                    "meeting_id": id_,
                    "number": "NUM01",
                    "number_value": 1,
                },
                f"motion/{id_ * 100}": {
                    "title": "Another",
                    "text": "<p>nice little</p>",
                    "reason": "motion",
                    "meeting_id": id_,
                    "number": "NUM02",
                    "number_value": 2,
                },
                f"motion_category/{id_}": {
                    "name": "Normal motion",
                    "prefix": "NORM",
                    "meeting_id": id_,
                },
                f"motion_category/{id_ * 10}": {
                    "name": "Other motion",
                    "prefix": "NORM",
                    "meeting_id": id_,
                },
                f"motion_category/{id_ * 100}": {
                    "name": "Other motion",
                    "prefix": "OTHER",
                    "meeting_id": id_,
                },
                f"motion_category/{id_ * 1000}": {
                    "name": "Other motion",
                    "meeting_id": id_,
                },
            }
        )


class MotionJsonUpload(BaseMotionJsonUpload):
    def test_json_upload_empty_data(self) -> None:
        response = self.request(
            "motion.json_upload",
            {"data": [], "meeting_id": 42},
        )
        self.assert_status_code(response, 400)
        assert "data.data must contain at least 1 items" in response.json["message"]

    def test_json_upload_unknown_meeting_id(self) -> None:
        self.setup_meeting_with_settings(42)
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "reason": "stuff"}],
                "meeting_id": 41,
            },
        )
        self.assert_status_code(response, 400)
        assert "Import tries to use non-existent meeting 41" in response.json["message"]

    def test_json_upload_create_missing_text(self) -> None:
        self.setup_meeting_with_settings(42)
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "reason": "stuff"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.ERROR
        assert (
            "Error: Text is required"
            in response.json["results"][0][0]["rows"][0]["messages"]
        )
        assert response.json["results"][0][0]["rows"][0]["data"]["text"] == {
            "value": "",
            "info": ImportState.ERROR,
        }

    def test_json_upload_create_missing_reason_although_required(self) -> None:
        self.setup_meeting_with_settings(42, is_reason_required=True)
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "text": "my"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.ERROR
        assert (
            "Error: Reason is required"
            in response.json["results"][0][0]["rows"][0]["messages"]
        )
        assert response.json["results"][0][0]["rows"][0]["data"]["reason"] == {
            "value": "",
            "info": ImportState.ERROR,
        }

    def assert_duplicate_numbers(self, number: str) -> None:
        self.setup_meeting_with_settings(22)
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "number": "NUM01",
                        "title": "test",
                        "text": "my",
                        "reason": "stuff",
                    },
                    {
                        "number": "NUM01",
                        "title": "test also",
                        "text": "<p>my other</p>",
                        "reason": "stuff",
                    },
                    {
                        "number": "NUM04",
                        "title": "test",
                        "text": "my",
                        "reason": "stuff",
                    },
                    {
                        "number": "NUM04",
                        "title": "test also",
                        "text": "<p>my other</p>",
                        "reason": "stuff",
                    },
                ],
                "meeting_id": 22,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 4
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.ERROR
        for i in range(4):
            assert result["rows"][i]["state"] == ImportState.ERROR
            assert (
                "Error: Found multiple motions with the same number"
                in result["rows"][i]["messages"]
            )
            assert result["rows"][i]["data"]["number"] == {
                "value": number,
                "info": ImportState.ERROR,
            }

    def test_duplicate_numbers_in_datastore(self) -> None:
        self.setup_meeting_with_settings(22)
        self.set_models(
            {
                "motion/23": {
                    "meeting_id": 22,
                    "number": "NUM01",
                    "title": "Title",
                    "text": "<p>Text</p>",
                },
                "meeting/22": {"motion_ids": [22, 23, 2200]},
            }
        )
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "number": "NUM01",
                        "title": "test",
                        "text": "my",
                        "reason": "stuff",
                    },
                ],
                "meeting_id": 22,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 1
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.ERROR
        assert result["rows"][0]["state"] == ImportState.ERROR
        assert sorted(result["rows"][0]["messages"]) == sorted(
            [
                "Error: Found multiple motions with the same number",
                "Error: Number is not unique.",
            ]
        )
        assert result["rows"][0]["data"]["number"] == {
            "value": "NUM01",
            "info": ImportState.ERROR,
        }

    def test_with_non_matching_verbose_users_with_errors(self) -> None:
        self.setup_meeting_with_settings(123)
        self.create_user("anotherOne", [123])
        knights = [
            "Sir Lancelot the Brave",
            "Sir Galahad the Pure",
            "Sir Bedivere the Wise",
            "Sir Robin the-not-quite-so-brave-as-Sir-Lancelot",
            "Arthur, King of the Britons",
        ]
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "title": "New",
                        "text": "motion",
                        "submitters_username": ["user123", "anotherOne"],
                        "submitters_verbose": knights,
                        "supporters_username": ["user123", "anotherOne"],
                        "supporters_verbose": knights,
                    },
                ],
                "meeting_id": 123,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 1
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.ERROR
        row = result["rows"][0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == [
            "Error: Verbose field is set and has more entries than the username field for submitters",
            "Error: Verbose field is set and has more entries than the username field for supporters",
        ]
        assert row["data"]["submitters_username"] == [
            {"info": ImportState.ERROR, "value": "user123"},
            {"info": ImportState.ERROR, "value": "anotherOne"},
        ]
        assert row["data"]["supporters_username"] == [
            {"info": ImportState.ERROR, "value": "user123"},
            {"info": ImportState.ERROR, "value": "anotherOne"},
        ]


class MotionJsonUploadForUseInImport(BaseMotionJsonUpload):
    def json_upload_amendment(self) -> None:
        self.create_meeting(42)
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "text": "my", "motion_amendment": "1"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 1
        assert response.json["results"][0][0]["state"] == ImportState.WARNING
        data = {
            "meeting_id": 42,
            "title": {"value": "test", "info": ImportState.DONE},
            "text": {"value": "<p>my</p>", "info": ImportState.DONE},
            "motion_amendment": {"value": True, "info": ImportState.WARNING},
            "submitters_username": [{"id": 1, "info": "generated", "value": "admin"}],
        }
        expected = {
            "state": ImportState.NEW,
            "messages": ["Amendments cannot be correctly imported"],
            "data": data,
        }
        assert response.json["results"][0][0]["rows"][0] == expected

    def json_upload_create_missing_title(self) -> None:
        self.setup_meeting_with_settings(42)
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"text": "my", "reason": "stuff"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.ERROR
        assert (
            "Error: Title is required"
            in response.json["results"][0][0]["rows"][0]["messages"]
        )

        assert response.json["results"][0][0]["rows"][0]["data"]["title"] == {
            "value": "",
            "info": ImportState.ERROR,
        }

    def json_upload_update_missing_title(self) -> None:
        self.setup_meeting_with_settings(42)
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"text": "my", "reason": "stuff", "number": "NUM01"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.DONE
        assert response.json["results"][0][0]["rows"][0]["messages"] == []
        assert "title" not in response.json["results"][0][0]["rows"][0]["data"]

    def json_upload_update_missing_reason_although_required(self) -> None:
        self.setup_meeting_with_settings(42, is_reason_required=True)
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "text": "my", "number": "NUM01"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.DONE
        assert response.json["results"][0][0]["rows"][0]["messages"] == []
        assert "reason" not in response.json["results"][0][0]["rows"][0]["data"]

    def json_upload_multi_row(self) -> None:
        self.setup_meeting_with_settings(1, is_set_number=True)
        self.set_user_groups(1, [1])
        self.create_user("anotherUser", [1])
        self.set_models(
            {
                "meeting/1": {"tag_ids": [1], "motion_block_ids": [1]},
                "tag/1": {"meeting_id": 1, "name": "Tag1"},
                "motion_block/1": {"meeting_id": 1, "title": "Block1"},
            }
        )
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "number": "NUM01",
                        "title": "first",
                        "text": "test my stuff",
                        "supporters_username": ["user1"],
                    },
                    {
                        "number": "NUM02",
                        "title": "then",
                        "reason": "test my other stuff",
                        "category_name": "Other motion",
                        "submitters_username": ["user1"],
                        "submitters_verbose": ["Lancelot the brave"],
                    },
                    {
                        "number": "NUM03",
                        "title": "also",
                        "text": "test the other peoples stuff",
                        "tags": ["Tag1"],
                    },
                    {
                        "title": "after that",
                        "text": "test even more stuff",
                        "supporters_username": ["user1", "admin", "anotherUser"],
                        "block": "Block1",
                    },
                    {
                        "title": "finally",
                        "text": "finish testing",
                        "category_name": "Other motion",
                        "category_prefix": "OTHER",
                    },
                ],
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        rows = response.json["results"][0][0]["rows"]
        simple_payload_addition = {
            "meeting_id": 1,
            "submitters_username": [
                {"id": 1, "info": ImportState.GENERATED, "value": "admin"}
            ],
        }
        assert len(rows) == 5
        row = rows[0]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == []
        assert row["data"] == {
            **simple_payload_addition,
            "id": 1,
            "number": {"value": "NUM01", "info": ImportState.DONE, "id": 1},
            "title": {"info": ImportState.DONE, "value": "first"},
            "text": {"info": ImportState.DONE, "value": "<p>test my stuff</p>"},
            "supporters_username": [
                {"id": 2, "info": ImportState.DONE, "value": "user1"}
            ],
        }
        row = rows[1]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == []
        assert row["data"] == {
            **simple_payload_addition,
            "id": 100,
            "number": {"value": "NUM02", "info": ImportState.DONE, "id": 100},
            "title": {"info": ImportState.DONE, "value": "then"},
            "reason": {"info": ImportState.DONE, "value": "test my other stuff"},
            "category_name": {
                "info": ImportState.DONE,
                "value": "Other motion",
                "id": 1000,
            },
            "submitters_username": [
                {"id": 2, "info": ImportState.DONE, "value": "user1"}
            ],
            "submitters_verbose": ["Lancelot the brave"],
        }
        row = rows[2]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == []
        assert row["data"] == {
            **simple_payload_addition,
            "number": {"value": "NUM03", "info": ImportState.DONE},
            "title": {"info": ImportState.DONE, "value": "also"},
            "text": {
                "info": ImportState.DONE,
                "value": "<p>test the other peoples stuff</p>",
            },
            "tags": [{"id": 1, "info": ImportState.DONE, "value": "Tag1"}],
        }
        row = rows[3]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == []
        assert row["data"] == {
            **simple_payload_addition,
            "number": {"value": "03", "info": ImportState.GENERATED},
            "title": {"info": ImportState.DONE, "value": "after that"},
            "text": {"info": ImportState.DONE, "value": "<p>test even more stuff</p>"},
            "supporters_username": [
                {"id": 2, "info": ImportState.DONE, "value": "user1"},
                {"id": 1, "info": ImportState.DONE, "value": "admin"},
                {"id": 3, "info": ImportState.DONE, "value": "anotherUser"},
            ],
            "block": {"id": 1, "info": ImportState.DONE, "value": "Block1"},
        }
        row = rows[4]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == []
        assert row["data"] == {
            **simple_payload_addition,
            "number": {"value": "OTHER01", "info": ImportState.GENERATED},
            "title": {"info": ImportState.DONE, "value": "finally"},
            "text": {"info": ImportState.DONE, "value": "<p>finish testing</p>"},
            "category_name": {
                "info": ImportState.DONE,
                "value": "Other motion",
                "id": 100,
            },
            "category_prefix": "OTHER",
        }

    def json_upload_simple_create(
        self,
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> None:
        self.setup_meeting_with_settings(42, is_reason_required, is_set_number)
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "text": "my", "reason": "stuff"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 1
        data = {
            "meeting_id": 42,
            "title": {"value": "test", "info": ImportState.DONE},
            "text": {"value": "<p>my</p>", "info": ImportState.DONE},
            "reason": {"value": "stuff", "info": ImportState.DONE},
            "submitters_username": [{"id": 1, "info": "generated", "value": "admin"}],
        }
        if is_set_number:
            data.update({"number": {"info": ImportState.GENERATED, "value": "03"}})
        expected = {
            "state": ImportState.NEW,
            "messages": [],
            "data": data,
        }
        assert response.json["results"][0][0]["rows"][0] == expected

    def json_upload_simple_update(
        self,
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> None:
        self.setup_meeting_with_settings(42, is_reason_required, is_set_number)
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "number": "NUM01",
                        "title": "test",
                        "text": "my",
                        "reason": "stuff",
                    }
                ],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 1
        expected = {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "id": 42,
                "meeting_id": 42,
                "number": {"id": 42, "value": "NUM01", "info": ImportState.DONE},
                "title": {"value": "test", "info": ImportState.DONE},
                "text": {"value": "<p>my</p>", "info": ImportState.DONE},
                "reason": {"value": "stuff", "info": ImportState.DONE},
                "submitters_username": [
                    {"id": 1, "info": "generated", "value": "admin"}
                ],
            },
        }
        assert response.json["results"][0][0]["rows"][0] == expected

    def json_upload_update_with_foreign_meeting(self) -> None:
        self.setup_meeting_with_settings(42, is_set_number=True)
        self.setup_meeting_with_settings(55)
        self.create_user("orgaUser")
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "number": "NUM01",
                        "title": "test",
                        "text": "my",
                        "reason": "stuff",
                        "category_name": "Normal motion",
                        "category_prefix": "NORM",
                        "submitters_username": ["user55"],
                        "supporters_username": ["user42", "nonExistant", "orgaUser"],
                    }
                ],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.WARNING
        assert response.json["results"][0][0]["headers"] == [
            {"property": "title", "type": "string", "is_object": True},
            {"property": "text", "type": "string", "is_object": True},
            {"property": "number", "type": "string", "is_object": True},
            {"property": "reason", "type": "string", "is_object": True},
            {
                "property": "submitters_verbose",
                "type": "string",
                "is_list": True,
                "is_hidden": True,
            },
            {
                "property": "submitters_username",
                "type": "string",
                "is_object": True,
                "is_list": True,
            },
            {
                "property": "supporters_verbose",
                "type": "string",
                "is_list": True,
                "is_hidden": True,
            },
            {
                "property": "supporters_username",
                "type": "string",
                "is_object": True,
                "is_list": True,
            },
            {"property": "category_name", "type": "string", "is_object": True},
            {"property": "category_prefix", "type": "string"},
            {"property": "tags", "type": "string", "is_object": True, "is_list": True},
            {"property": "block", "type": "string", "is_object": True},
            {
                "property": "motion_amendment",
                "type": "boolean",
                "is_object": True,
                "is_hidden": True,
            },
        ]
        assert response.json["results"][0][0]["statistics"] == [
            {"name": "total", "value": 1},
            {"name": "created", "value": 0},
            {"name": "updated", "value": 1},
            {"name": "error", "value": 0},
            {"name": "warning", "value": 1},
        ]
        assert len(response.json["results"][0][0]["rows"]) == 1
        assert response.json["results"][0][0]["rows"][0]["state"] == ImportState.DONE
        messages = response.json["results"][0][0]["rows"][0]["messages"]
        assert len(messages) == 2
        assert messages[0] == "Could not find at least one submitter: user55"
        assert messages[1].startswith("Could not find at least one supporter:")
        assert " nonExistant" in messages[1]
        assert " orgaUser" in messages[1]
        assert response.json["results"][0][0]["rows"][0]["data"] == {
            "number": {"value": "NUM01", "info": ImportState.DONE, "id": 42},
            "title": {"value": "test", "info": ImportState.DONE},
            "text": {"value": "<p>my</p>", "info": ImportState.DONE},
            "reason": {"value": "stuff", "info": ImportState.DONE},
            "category_name": {
                "value": "Normal motion",
                "info": ImportState.DONE,
                "id": 42,
            },
            "category_prefix": "NORM",
            "meeting_id": 42,
            "submitters_username": [
                {"value": "user55", "info": ImportState.WARNING},
                {"id": 1, "info": ImportState.GENERATED, "value": "admin"},
            ],
            "id": 42,
            "supporters_username": [
                {"value": "user42", "info": ImportState.DONE, "id": 2},
                {"value": "nonExistant", "info": ImportState.WARNING},
                {"value": "orgaUser", "info": ImportState.WARNING},
            ],
        }

    def json_upload_custom_number_create(self) -> None:
        self.assert_custom_number_create()

    def json_upload_custom_number_create_with_set_number(self) -> None:
        self.assert_custom_number_create(True)

    def assert_custom_number_create(self, is_set_number: bool = False) -> None:
        self.setup_meeting_with_settings(42, is_set_number)
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "number": "Z01",
                        "title": "test",
                        "text": "my",
                        "reason": "stuff",
                        "category_name": "Other motion",
                        "category_prefix": "NORM",
                    }
                ],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        rows = response.json["results"][0][0]["rows"]
        assert len(rows) == 1
        assert rows[0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "meeting_id": 42,
                "number": {"value": "Z01", "info": ImportState.DONE},
                "title": {"value": "test", "info": ImportState.DONE},
                "text": {"value": "<p>my</p>", "info": ImportState.DONE},
                "reason": {"value": "stuff", "info": ImportState.DONE},
                "submitters_username": [
                    {"id": 1, "info": "generated", "value": "admin"}
                ],
                "category_prefix": "NORM",
                "category_name": {
                    "info": ImportState.DONE,
                    "value": "Other motion",
                    "id": 420,
                },
            },
        }

    def json_upload_with_warnings(self) -> None:
        self.setup_meeting_with_settings(10)
        self.set_models(
            {
                "motion_category/100000": {
                    "name": "Normal motion",
                    "prefix": "NORM",
                    "meeting_id": 10,
                },
                "meeting/10": {"motion_category_ids": [10, 100, 1000, 10000, 100000]},
            }
        )
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "number": "NUM01",
                        "title": "Up",
                        "text": "date",
                        "category_name": "Unknown",
                        "category_prefix": "CAT",
                        "submitters_username": ["user10", "user10"],
                    },
                    {
                        "title": "New",
                        "text": "motion",
                        "category_prefix": "Shouldn't be found",
                        "supporters_username": ["user10", "user10", "user10", "user10"],
                    },
                    {
                        "title": "Newer",
                        "text": "motion",
                        "category_name": "Normal motion",
                        "category_prefix": "NORM",
                        "submitters_username": ["nonExistant"],
                        "supporters_username": ["nonExistant", "nonExistant"],
                    },
                ],
                "meeting_id": 10,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 3
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.WARNING
        row = result["rows"][0]
        assert row["state"] == ImportState.DONE
        assert sorted(row["messages"]) == sorted(
            [
                "Category could not be found",
                "At least one submitter has been referenced multiple times: user10",
            ]
        )
        assert row["data"] == {
            "number": {"value": "NUM01", "info": ImportState.DONE, "id": 10},
            "title": {"value": "Up", "info": ImportState.DONE},
            "text": {"value": "<p>date</p>", "info": ImportState.DONE},
            "category_name": {"value": "Unknown", "info": ImportState.WARNING},
            "category_prefix": "CAT",
            "meeting_id": 10,
            "submitters_username": [
                {"value": "user10", "info": ImportState.DONE, "id": 2},
                {"value": "user10", "info": ImportState.WARNING},
            ],
            "id": 10,
        }
        row = result["rows"][1]
        assert row["state"] == ImportState.NEW
        assert sorted(row["messages"]) == sorted(
            [
                "Category could not be found",
                "At least one supporter has been referenced multiple times: user10",
            ]
        )
        assert row["data"] == {
            "title": {"value": "New", "info": ImportState.DONE},
            "text": {"value": "<p>motion</p>", "info": ImportState.DONE},
            "category_name": {"value": "", "info": ImportState.WARNING},
            "category_prefix": "Shouldn't be found",
            "meeting_id": 10,
            "submitters_username": [
                {"value": "admin", "info": ImportState.GENERATED, "id": 1}
            ],
            "supporters_username": [
                {"value": "user10", "info": ImportState.DONE, "id": 2},
                {"value": "user10", "info": ImportState.WARNING},
                {"value": "user10", "info": ImportState.WARNING},
                {"value": "user10", "info": ImportState.WARNING},
            ],
        }
        row = result["rows"][2]
        assert row["state"] == ImportState.NEW
        assert sorted(row["messages"]) == sorted(
            [
                "Category could not be found",
                "Could not find at least one submitter: nonExistant",
                "At least one supporter has been referenced multiple times: nonExistant",
                "Could not find at least one supporter: nonExistant",
            ]
        )
        assert row["data"] == {
            "title": {"value": "Newer", "info": ImportState.DONE},
            "text": {"value": "<p>motion</p>", "info": ImportState.DONE},
            "category_name": {"value": "Normal motion", "info": ImportState.WARNING},
            "category_prefix": "NORM",
            "meeting_id": 10,
            "submitters_username": [
                {"value": "nonExistant", "info": ImportState.WARNING},
                {"value": "admin", "info": ImportState.GENERATED, "id": 1},
            ],
            "supporters_username": [
                {"value": "nonExistant", "info": ImportState.WARNING},
                {"value": "nonExistant", "info": ImportState.WARNING},
            ],
        }

    def json_upload_with_non_matching_verbose_users_okay(self) -> None:
        self.setup_meeting_with_settings(123)
        self.create_user("anotherOne", [123])
        knights = [
            "Sir Lancelot the Brave",
            "Sir Galahad the Pure",
            "Sir Bedivere the Wise",
            "Sir Robin the-not-quite-so-brave-as-Sir-Lancelot",
            "Arthur, King of the Britons",
        ]
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "number": "NUM01",
                        "title": "Up",
                        "text": "date",
                        "submitters_username": ["user123", "anotherOne"],
                        "submitters_verbose": [knights[0]],
                        "supporters_username": ["user123", "anotherOne"],
                        "supporters_verbose": [knights[0]],
                    },
                    {
                        "title": "Newer",
                        "text": "motion",
                        "submitters_verbose": knights,
                        "supporters_verbose": knights,
                    },
                ],
                "meeting_id": 123,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 2
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.DONE
        row = result["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["messages"] == []
        assert row["data"]["submitters_username"] == [
            {"id": 2, "info": ImportState.DONE, "value": "user123"},
            {"id": 3, "info": ImportState.DONE, "value": "anotherOne"},
        ]
        assert row["data"]["supporters_username"] == [
            {"id": 2, "info": ImportState.DONE, "value": "user123"},
            {"id": 3, "info": ImportState.DONE, "value": "anotherOne"},
        ]
        row = result["rows"][1]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == []
        assert row["data"]["submitters_username"] == [
            {"value": "admin", "info": ImportState.GENERATED, "id": 1}
        ]
        assert row["data"]["submitters_verbose"] == knights
        assert "supporters_username" not in row["data"]
        assert row["data"]["supporters_verbose"] == knights

    def json_upload_with_tags_and_blocks(self) -> None:
        self.setup_meeting_with_settings(42)
        self.setup_meeting_with_settings(55)
        self.set_models(
            {
                "meeting/42": {
                    "tag_ids": [1, 2, 3, 4],
                    "motion_block_ids": [1, 2, 3, 4],
                },
                "meeting/55": {"tag_ids": [5, 6], "motion_block_ids": [5, 6]},
                "tag/1": {"name": "Tag-liatelle", "meeting_id": 42},
                "tag/2": {"name": "Tag-you're-it", "meeting_id": 42},
                "tag/3": {"name": "Tag-ether", "meeting_id": 42},
                "tag/4": {"name": "Tag-ether", "meeting_id": 42},
                "tag/5": {"name": "Tag-you're-it", "meeting_id": 55},
                "tag/6": {"name": "Price tag", "meeting_id": 55},
                "motion_block/1": {"title": "Blockolade", "meeting_id": 42},
                "motion_block/2": {"title": "Blockodile", "meeting_id": 42},
                "motion_block/3": {"title": "Block chain", "meeting_id": 42},
                "motion_block/4": {"title": "Block chain", "meeting_id": 42},
                "motion_block/5": {"title": "Blockodile", "meeting_id": 55},
                "motion_block/6": {"title": "Blockoli", "meeting_id": 55},
            }
        )
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "number": "NUM01",
                        "title": "Up",
                        "text": "date",
                        "tags": [
                            "Tag-liatelle",
                            "Tag-you're-it",
                            "Tag-ether",
                            "Price tag",
                            "Not a tag",
                        ],
                        "block": "Blockolade",
                    },
                    {
                        "title": "New",
                        "text": "motion",
                        "tags": [
                            "Tag-liatelle",
                            "Tag-liatelle",
                            "Tag-you're-it",
                            "Tag-you're-it",
                        ],
                        "block": "Blockodile",
                    },
                    {"title": "Newer", "text": "motion", "block": "Block chain"},
                    {"title": "Newest", "text": "motion", "block": "Blockoli"},
                ],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.WARNING
        assert len(result["rows"]) == 4
        row = result["rows"][0]
        assert row["state"] == ImportState.DONE
        assert row["messages"][0].startswith("Could not find at least one tag:")
        assert " Not a tag" in row["messages"][0]
        assert " Price tag" in row["messages"][0]
        assert row["messages"][1] == "Found multiple tags with the same name: Tag-ether"
        assert row["data"]["tags"] == [
            {"value": "Tag-liatelle", "info": "done", "id": 1},
            {"value": "Tag-you're-it", "info": "done", "id": 2},
            {"value": "Tag-ether", "info": "warning"},
            {"value": "Price tag", "info": "warning"},
            {"value": "Not a tag", "info": "warning"},
        ]
        assert row["data"]["block"] == {"value": "Blockolade", "info": "done", "id": 1}
        row = result["rows"][1]
        assert row["state"] == ImportState.NEW
        assert len(row["messages"]) == 1
        assert row["messages"][0].startswith(
            "At least one tag has been referenced multiple times:"
        )
        assert "Tag-liatelle" in row["messages"][0]
        assert "Tag-you're-it" in row["messages"][0]
        assert row["data"]["tags"] == [
            {"value": "Tag-liatelle", "info": "done", "id": 1},
            {"value": "Tag-liatelle", "info": ImportState.WARNING},
            {"value": "Tag-you're-it", "info": "done", "id": 2},
            {"value": "Tag-you're-it", "info": ImportState.WARNING},
        ]
        assert row["data"]["block"] == {"value": "Blockodile", "info": "done", "id": 2}
        row = result["rows"][2]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == ["Found multiple motion blocks with the same name"]
        assert row["data"]["block"] == {
            "value": "Block chain",
            "info": ImportState.WARNING,
        }
        row = result["rows"][3]
        assert row["state"] == ImportState.NEW
        assert row["messages"] == ["Could not find motion block"]
        assert row["data"]["block"] == {
            "value": "Blockoli",
            "info": ImportState.WARNING,
        }
