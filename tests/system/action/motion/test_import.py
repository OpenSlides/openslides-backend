# from typing import Any

from openslides_backend.action.mixins.import_mixins import ImportState

# from .test_json_upload import MotionImportTestMixin
from .test_json_upload import MotionJsonUploadForUseInImport


class MotionImport(MotionJsonUploadForUseInImport):

    def test_import_database_corrupt(self) -> None:
        self.create_meeting(42)
        self.set_models(
            {
                "import_preview/2": {
                    "state": ImportState.DONE,
                    "name": "motion",
                    "result": {
                        "rows": [
                            {
                                "state": (ImportState.DONE),
                                "messages": [],
                                "data": {
                                    "title": {
                                        "value": "New",
                                        "info": ImportState.DONE,
                                    },
                                    "text": {
                                        "value": "Motion",
                                        "info": ImportState.DONE,
                                    },
                                    "reason": {"value": "", "info": ImportState.DONE},
                                    "supporters_username": [],
                                    "category_name": {
                                        "value": "",
                                        "info": ImportState.DONE,
                                    },
                                    "tags": [],
                                    "block": {"value": "", "info": ImportState.DONE},
                                    "number": {
                                        "info": ImportState.DONE,
                                        "id": 101,
                                        "value": "NUM01",
                                    },
                                    "submitters_username": [
                                        {
                                            "info": ImportState.DONE,
                                            "id": 12345678,
                                            "value": "bob",
                                        }
                                    ],
                                    "id": 101,
                                    "meeting_id": 42,
                                },
                            }
                        ],
                    },
                },
                "user/12345678": {
                    "username": "bob",
                    "meeting_ids": [42],
                    "meeting_user_ids": [12345678],
                },
                "meeting_user/12345678": {},
                "user/123456789": {
                    "username": "bob",
                    "meeting_ids": [42],
                    "meeting_user_ids": [123456789],
                },
                "meeting_user/123456789": {},
                "meeting/42": {"meeting_user_ids": [12345678, 123456789]},
            }
        )
        response = self.request("motion.import", {"id": 2, "import": True})
        self.assert_status_code(response, 400)
        assert (
            "Database corrupt: Found multiple users with the username bob."
            in response.json["message"]
        )

    def test_import_abort(self) -> None:
        self.create_meeting(42)
        self.set_models(
            {
                "import_preview/2": {
                    "state": ImportState.DONE,
                    "name": "motion",
                    "result": {
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "title": {
                                        "value": "New",
                                        "info": ImportState.DONE,
                                    },
                                    "text": {
                                        "value": "Motion",
                                        "info": ImportState.DONE,
                                    },
                                    "number": {"value": "", "info": ImportState.DONE},
                                    "reason": {"value": "", "info": ImportState.DONE},
                                    "submitters_username": [
                                        {
                                            "value": "admin",
                                            "info": ImportState.GENERATED,
                                            "id": 1,
                                        }
                                    ],
                                    "supporters_username": [],
                                    "category_name": {
                                        "value": "",
                                        "info": ImportState.DONE,
                                    },
                                    "tags": [],
                                    "block": {"value": "", "info": ImportState.DONE},
                                    "meeting_id": 42,
                                },
                            }
                        ],
                    },
                },
            }
        )
        response = self.request("motion.import", {"id": 2, "import": False})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("import_preview/2")
        self.assert_model_not_exists("motion/1")

    def test_import_wrong_import_preview(self) -> None:
        self.create_meeting(42)
        self.set_models(
            {
                "import_preview/3": {"result": None},
                "import_preview/4": {
                    "state": ImportState.DONE,
                    "name": "topic",
                    "result": {
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "title": {"value": "test", "info": ImportState.NEW},
                                    "meeting_id": 42,
                                },
                            },
                        ],
                    },
                },
            }
        )
        response = self.request("motion.import", {"id": 3, "import": True})
        self.assert_status_code(response, 400)
        assert (
            "Wrong id doesn't point on motion import data." in response.json["message"]
        )

    def test_import_wrong_meeting_model_import_preview(self) -> None:
        self.create_meeting(42)
        self.set_models(
            {
                "import_preview/4": {
                    "state": ImportState.DONE,
                    "name": "topic",
                    "result": {
                        "rows": [
                            {
                                "state": ImportState.NEW,
                                "messages": [],
                                "data": {
                                    "title": {"value": "test", "info": ImportState.NEW},
                                    "meeting_id": 42,
                                },
                            },
                        ],
                    },
                },
            }
        )
        response = self.request("motion.import", {"id": 4, "import": True})
        self.assert_status_code(response, 400)
        assert (
            "Wrong id doesn't point on motion import data." in response.json["message"]
        )

    def test_json_upload_amendment(self) -> None:
        self.json_upload_amendment()
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.DONE

    def test_json_upload_multi_row(self) -> None:
        self.json_upload_multi_row()
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/42",
            {
                "title": "first",
                "text": "<p>test my stuff</p>",
                "reason": "motion",  # retained from before
                "supporter_meeting_user_ids": [1],
                "submitter_ids": [1],
            },
        )
        self.assert_model_exists("motion_submitter/1", {"meeting_user_id": 2})
        self.assert_model_exists("meeting_user/1", {"user_id": 2})
        self.assert_model_exists("meeting_user/2", {"user_id": 1})
        self.assert_model_exists(
            "motion/4200",
            {
                "title": "then",
                "text": "<p>nice little</p>",  # retained from before
                "reason": "test my other stuff",
                "submitter_ids": [2],
                "category_id": 1000,
            },
        )
        self.assert_model_exists("motion_submitter/2", {"meeting_user_id": 1})
        self.assert_model_exists(
            "motion/4201",
            {
                "number": "NUM03",
                "title": "also",
                "text": "<p>test the other peoples stuff</p>",
                "submitter_ids": [3],
            },
        )
        self.assert_model_exists("motion_submitter/3", {"meeting_user_id": 1})
        self.assert_model_exists(
            "motion/4202",
            {
                "number": "03",
                "title": "after that",
                "text": "<p>test even more stuff</p>",
                "submitter_ids": [4],
                "supporter_meeting_user_ids": [1, 2],
            },
        )
        self.assert_model_exists("motion_submitter/4", {"meeting_user_id": 1})
        self.assert_model_exists(
            "motion/4203",
            {
                "number": "OTHER01",
                "title": "finally",
                "text": "<p>finish testing</p>",
                "submitter_ids": [5],
                "category_id": 100,
            },
        )
        self.assert_model_exists("motion_submitter/5", {"meeting_user_id": 1})

    def test_simple_create(self) -> None:
        self.json_upload_simple_create()
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        motion = self.assert_model_exists(
            "motion/4201",
            {
                "title": "test",
                "text": "<p>my</p>",
                "reason": "stuff",
                "submitter_ids": [1],
            },
        )
        assert "number" not in motion
        self.assert_model_exists("motion_submitter/1", {"meeting_user_id": 2})
        self.assert_model_exists("meeting_user/2", {"user_id": 1})

    def test_simple_create_with_reason_required(self) -> None:
        self.json_upload_simple_create(True)
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        motion = self.assert_model_exists(
            "motion/4201",
            {
                "title": "test",
                "text": "<p>my</p>",
                "reason": "stuff",
                "submitter_ids": [1],
            },
        )
        assert "number" not in motion
        self.assert_model_exists("motion_submitter/1", {"meeting_user_id": 2})
        self.assert_model_exists("meeting_user/2", {"user_id": 1})

    def test_simple_create_with_set_number(self) -> None:
        self.json_upload_simple_create(is_set_number=True)
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/4201",
            {
                "number": "03",
                "title": "test",
                "text": "<p>my</p>",
                "reason": "stuff",
                "submitter_ids": [1],
            },
        )
        self.assert_model_exists("motion_submitter/1", {"meeting_user_id": 2})
        self.assert_model_exists("meeting_user/2", {"user_id": 1})

    def test_simple_update(self) -> None:
        self.json_upload_simple_update()
        self.assert_simple_update_successful()

    def test_simple_update_with_reason_required(self) -> None:
        self.json_upload_simple_update(True)
        self.assert_simple_update_successful()

    def test_simple_update_with_set_number(self) -> None:
        self.json_upload_simple_update(is_set_number=True)
        self.assert_simple_update_successful()

    def assert_simple_update_successful(self) -> None:
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/42",
            {
                "number": "NUM01",
                "title": "test",
                "text": "<p>my</p>",
                "reason": "stuff",
                "submitter_ids": [1],
            },
        )
        self.assert_model_exists("motion_submitter/1", {"meeting_user_id": 2})
        self.assert_model_exists("meeting_user/2", {"user_id": 1})

    def test_json_upload_update_with_foreign_meeting(self) -> None:
        self.json_upload_update_with_foreign_meeting()
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/42",
            {
                "number": "NUM01",
                "title": "test",
                "text": "<p>my</p>",
                "reason": "stuff",
                "category_id": 42,
                "submitter_ids": [1],
                "supporter_meeting_user_ids": [1],
            },
        )
        self.assert_model_exists("motion_submitter/1", {"meeting_user_id": 3})
        self.assert_model_exists("meeting_user/3", {"user_id": 1})

    def test_json_upload_custom_number_create(self) -> None:
        self.json_upload_custom_number_create()
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/4201",
            {
                "number": "Z01",
                "title": "test",
                "text": "<p>my</p>",
                "reason": "stuff",
                "category_id": 420,
            },
        )

    def test_json_upload_custom_number_create_with_set_number(self) -> None:
        self.json_upload_custom_number_create_with_set_number()
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/4201",
            {
                "number": "Z01",
                "title": "test",
                "text": "<p>my</p>",
                "reason": "stuff",
                "category_id": 420,
            },
        )

    def test_with_warnings(self) -> None:
        self.json_upload_with_warnings()
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        motion = self.assert_model_exists("motion/10")
        assert "category_id" not in motion
        assert motion["submitter_ids"] == [3]
        self.assert_model_exists("motion_submitter/3", {"meeting_user_id": 1})
        self.assert_model_exists("meeting_user/1", {"user_id": 2})

        motion = self.assert_model_exists("motion/1001")
        assert "category_id" not in motion
        assert motion["submitter_ids"] == [1]
        self.assert_model_exists("motion_submitter/1", {"meeting_user_id": 2})
        self.assert_model_exists("meeting_user/2", {"user_id": 1})
        assert motion["supporter_meeting_user_ids"] == [1]

        motion = self.assert_model_exists("motion/1002")
        assert "category_id" not in motion
        assert motion["submitter_ids"] == [2]
        self.assert_model_exists("motion_submitter/2", {"meeting_user_id": 2})
        assert len(motion["supporter_meeting_user_ids"]) == 0

    def test_with_tags_and_blocks(self) -> None:
        self.json_upload_with_tags_and_blocks()
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/42",
            {
                "number": "NUM01",
                "tag_ids": [1, 2],
                "block_id": 1,
            },
        )
        self.assert_model_exists("motion/5501", {"tag_ids": [1, 2], "block_id": 2})
        mot3 = self.assert_model_exists("motion/5502", {"tag_ids": []})
        assert "block_id" not in mot3
        mot4 = self.assert_model_exists("motion/5503", {"tag_ids": []})
        assert "block_id" not in mot4
