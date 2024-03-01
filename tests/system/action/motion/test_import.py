from openslides_backend.action.mixins.import_mixins import ImportState

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

    def test_import_non_existant_ids(self) -> None:
        self.create_meeting(42)
        preview_rows = [
            {
                "state": ImportState.DONE,
                "messages": [],
                "data": {
                    "id": 1,
                    "title": {
                        "value": "Update",
                        "info": ImportState.DONE,
                    },
                    "text": {
                        "value": "<p>of non-existant motion</>",
                        "info": ImportState.DONE,
                    },
                    "number": {
                        "id": 1,
                        "value": "NOMNOMNOM1",
                        "info": ImportState.DONE,
                    },
                    "submitters_username": [
                        {
                            "value": "nonExistantUser",
                            "info": ImportState.DONE,
                            "id": 2,
                        }
                    ],
                    "supporters_username": [
                        {
                            "value": "NoOne",
                            "info": ImportState.DONE,
                            "id": 3,
                        }
                    ],
                    "category_name": {
                        "id": 8,
                        "value": "NonCategory",
                        "info": ImportState.DONE,
                    },
                    "tags": [
                        {
                            "id": 9,
                            "value": "NonTag",
                            "info": ImportState.DONE,
                        }
                    ],
                    "block": {"id": 9, "value": "NonBlock", "info": ImportState.DONE},
                    "meeting_id": 42,
                },
            },
            {
                "state": ImportState.NEW,
                "messages": [],
                "data": {
                    "title": {
                        "value": "Create",
                        "info": ImportState.DONE,
                    },
                    "text": {
                        "value": "<p>a new motion</p>",
                        "info": ImportState.DONE,
                    },
                    "number": {"value": "NEW", "info": ImportState.DONE},
                    "submitters_username": [
                        {
                            "value": "nonUser",
                            "info": ImportState.DONE,
                            "id": 4,
                        }
                    ],
                    "supporters_username": [
                        {
                            "value": "NoOne",
                            "info": ImportState.DONE,
                            "id": 5,
                        }
                    ],
                    "category_name": {
                        "id": 10,
                        "value": "NonCategoryTwoElectricBoogaloo",
                        "info": ImportState.DONE,
                    },
                    "tags": [
                        {
                            "id": 11,
                            "value": "TagNot",
                            "info": ImportState.DONE,
                        }
                    ],
                    "block": {
                        "id": 12,
                        "value": "JustBlockIt",
                        "info": ImportState.DONE,
                    },
                    "meeting_id": 42,
                },
            },
        ]
        self.set_models(
            {
                "import_preview/2": {
                    "state": ImportState.DONE,
                    "name": "motion",
                    "result": {
                        "rows": preview_rows,
                    },
                },
            }
        )
        response = self.request("motion.import", {"id": 2, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion/1")
        self.assert_model_not_exists("motion/2")
        meeting = self.assert_model_exists("meeting/42")
        assert "motion_ids" not in meeting
        response_rows = response.json["results"][0][0]["rows"]
        assert response_rows[0]["data"] == {
            "id": 1,
            "tags": [{"info": "error", "value": "NonTag"}],
            "text": {"info": "done", "value": "<p>of non-existant motion</>"},
            "block": {"value": "NonBlock", "info": "error"},
            "title": {"info": "done", "value": "Update"},
            "number": {"id": 1, "info": "error", "value": "NOMNOMNOM1"},
            "meeting_id": 42,
            "category_name": {"value": "NonCategory", "info": "error"},
            "submitters_username": [{"info": "error", "value": "nonExistantUser"}],
            "supporters_username": [{"info": "error", "value": "NoOne"}],
        }
        assert sorted(response_rows[0]["messages"]) == sorted(
            [
                "Error: Couldn't find motion block anymore",
                "Error: Couldn't find supporter anymore: NoOne",
                "Error: Couldn't find tag anymore: NonTag",
                "Error: Category could not be found anymore",
                "Error: Couldn't find submitter anymore: nonExistantUser",
                "Error: Motion 1 not found anymore for updating motion 'NOMNOMNOM1'.",
            ]
        )
        assert response_rows[1]["data"] == {
            "tags": [{"info": "error", "value": "TagNot"}],
            "text": {"info": "done", "value": "<p>a new motion</p>"},
            "block": {"value": "JustBlockIt", "info": "error"},
            "title": {"info": "done", "value": "Create"},
            "number": {"info": "done", "value": "NEW"},
            "meeting_id": 42,
            "category_name": {
                "value": "NonCategoryTwoElectricBoogaloo",
                "info": "error",
            },
            "submitters_username": [{"info": "error", "value": "nonUser"}],
            "supporters_username": [{"info": "error", "value": "NoOne"}],
        }
        assert sorted(response_rows[1]["messages"]) == sorted(
            [
                "Error: Couldn't find motion block anymore",
                "Error: Couldn't find supporter anymore: NoOne",
                "Error: Couldn't find tag anymore: TagNot",
                "Error: Category could not be found anymore",
                "Error: Couldn't find submitter anymore: nonUser",
            ]
        )

    def test_import_with_deleted_references(self) -> None:
        self.json_upload_multi_row()
        self.request("motion.delete", {"id": 100})
        self.request("user.delete", {"id": 2})
        self.request("meeting_user.delete", {"id": 3})
        self.request("motion_category.delete", {"id": 100})
        self.request("motion_category.delete", {"id": 1000})
        self.request("motion_block.delete", {"id": 1})
        self.request("tag.delete", {"id": 1})
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "A",
                "text": "<p>nice little</p>",
                "reason": "motion",
            },
        )
        self.assert_model_exists("meeting/1", {"motion_ids": [1]})
        self.assert_model_deleted("motion/100")
        self.assert_model_not_exists("motion/101")
        self.assert_model_not_exists("motion/102")
        self.assert_model_not_exists("motion/103")
        rows = response.json["results"][0][0]["rows"]
        assert len(rows) == 5
        row = rows[0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == ["Error: Couldn't find supporter anymore: user1"]
        assert row["data"]["supporters_username"] == [
            {"info": ImportState.ERROR, "value": "user1"}
        ]
        row = rows[1]
        assert row["state"] == ImportState.ERROR
        assert sorted(row["messages"]) == sorted(
            [
                "Error: Motion 100 not found anymore for updating motion 'NUM02'.",
                "Error: Couldn't find submitter anymore: user1",
                "Error: Category could not be found anymore",
            ]
        )
        assert row["data"]["number"] == {
            "id": 100,
            "value": "NUM02",
            "info": ImportState.ERROR,
        }
        assert row["data"]["category_name"] == {
            "info": ImportState.ERROR,
            "value": "Other motion",
        }
        assert row["data"]["submitters_username"] == [
            {"info": ImportState.ERROR, "value": "user1"}
        ]
        row = rows[2]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == ["Error: Couldn't find tag anymore: Tag1"]
        assert row["data"]["tags"] == [{"info": ImportState.ERROR, "value": "Tag1"}]
        row = rows[3]
        assert row["state"] == ImportState.ERROR
        assert sorted(row["messages"]) == sorted(
            [
                "Error: Couldn't find supporter anymore: user1, anotherUser",
                "Error: Couldn't find motion block anymore",
            ]
        )
        assert row["data"]["supporters_username"] == [
            {"info": ImportState.ERROR, "value": "user1"},
            {"id": 1, "info": ImportState.DONE, "value": "admin"},
            {"info": ImportState.ERROR, "value": "anotherUser"},
        ]
        assert row["data"]["block"] == {"info": ImportState.ERROR, "value": "Block1"}
        row = rows[4]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == ["Error: Category could not be found anymore"]
        assert row["data"]["category_name"] == {
            "info": ImportState.ERROR,
            "value": "Other motion",
        }

    def test_import_with_changed_references(self) -> None:
        self.json_upload_multi_row()
        self.set_models(
            {
                "user/2": {"username": "changedName"},
                "user/3": {"username": "changedNameToo"},
                "motion_category/100": {"name": "changedName"},
                "motion_category/1000": {"prefix": "changedPREFIX"},
                "motion_block/1": {"title": "changedTitle"},
                "tag/1": {"name": "changedName"},
            }
        )
        self.create_user("anotherUser", [1])
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        rows = response.json["results"][0][0]["rows"]
        assert len(rows) == 5
        row = rows[0]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == ["Error: Couldn't find supporter anymore: user1"]
        assert row["data"]["supporters_username"] == [
            {"info": ImportState.ERROR, "value": "user1"}
        ]
        row = rows[1]
        assert row["state"] == ImportState.ERROR
        assert sorted(row["messages"]) == sorted(
            [
                "Error: Couldn't find submitter anymore: user1",
                "Error: Category could not be found anymore",
            ]
        )
        assert row["data"]["category_name"] == {
            "info": ImportState.ERROR,
            "value": "Other motion",
        }
        assert row["data"]["submitters_username"] == [
            {"info": ImportState.ERROR, "value": "user1"}
        ]
        row = rows[2]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == ["Error: Couldn't find tag anymore: Tag1"]
        assert row["data"]["tags"] == [{"info": ImportState.ERROR, "value": "Tag1"}]
        row = rows[3]
        assert row["state"] == ImportState.ERROR
        assert sorted(row["messages"]) == sorted(
            [
                "Error: Supporter search didn't deliver the same result as in the preview: anotherUser",
                "Error: Couldn't find motion block anymore",
                "Error: Couldn't find supporter anymore: user1",
            ]
        )
        assert row["data"]["supporters_username"] == [
            {"info": ImportState.ERROR, "value": "user1"},
            {"id": 1, "info": ImportState.DONE, "value": "admin"},
            {"info": ImportState.ERROR, "value": "anotherUser"},
        ]
        assert row["data"]["block"] == {"info": ImportState.ERROR, "value": "Block1"}
        row = rows[4]
        assert row["state"] == ImportState.ERROR
        assert row["messages"] == ["Error: Category could not be found anymore"]
        assert row["data"]["category_name"] == {
            "info": ImportState.ERROR,
            "value": "Other motion",
        }

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

    def test_json_upload_with_errors(self) -> None:
        self.json_upload_create_missing_title()
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 400)
        assert "Error in import. Data will not be imported." in response.json["message"]

    def test_json_upload_update_missing_title(self) -> None:
        self.json_upload_update_missing_title()
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.DONE
        self.assert_model_exists("motion/42", {"title": "A"})

    def test_json_upload_update_missing_reason_although_required(self) -> None:
        self.json_upload_update_missing_reason_although_required()
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.DONE
        self.assert_model_exists("motion/42", {"reason": "motion"})

    def test_json_upload_multi_row(self) -> None:
        self.json_upload_multi_row()
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "first",
                "text": "<p>test my stuff</p>",
                "reason": "motion",  # retained from before
                "supporter_meeting_user_ids": [1],
                "submitter_ids": [4],
            },
        )
        self.assert_model_exists("motion_submitter/4", {"meeting_user_id": 2})
        self.assert_model_exists("meeting_user/1", {"user_id": 2})
        self.assert_model_exists("meeting_user/2", {"user_id": 1})
        self.assert_model_exists(
            "motion/100",
            {
                "title": "then",
                "text": "<p>nice little</p>",  # retained from before
                "reason": "test my other stuff",
                "submitter_ids": [5],
                "category_id": 1000,
            },
        )
        self.assert_model_exists("motion_submitter/5", {"meeting_user_id": 1})
        self.assert_model_exists(
            "motion/101",
            {
                "number": "NUM03",
                "title": "also",
                "text": "<p>test the other peoples stuff</p>",
                "submitter_ids": [1],
                "tag_ids": [1],
            },
        )
        self.assert_model_exists("motion_submitter/1", {"meeting_user_id": 2})
        self.assert_model_exists(
            "motion/102",
            {
                "number": "03",
                "title": "after that",
                "text": "<p>test even more stuff</p>",
                "submitter_ids": [2],
                "supporter_meeting_user_ids": [1, 2, 3],
                "block_id": 1,
            },
        )
        self.assert_model_exists("motion_submitter/2", {"meeting_user_id": 2})
        self.assert_model_exists(
            "motion/103",
            {
                "number": "OTHER01",
                "title": "finally",
                "text": "<p>finish testing</p>",
                "submitter_ids": [3],
                "category_id": 100,
            },
        )
        self.assert_model_exists("motion_submitter/3", {"meeting_user_id": 2})

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

    def test_with_non_matching_verbose_users_okay(self) -> None:
        self.json_upload_with_non_matching_verbose_users_okay()
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/123",
            {
                "number": "NUM01",
                "title": "Up",
                "text": "<p>date</p>",
                "submitter_ids": [2, 3],
                "supporter_meeting_user_ids": [1, 2],
            },
        )
        newMotion = self.assert_model_exists(
            "motion/12301",
            {
                "title": "Newer",
                "text": "<p>motion</p>",
                "submitter_ids": [1],
            },
        )
        assert len(newMotion.get("supporter_meeting_user_ids", [])) == 0
        self.assert_model_exists(
            "meeting_user/1", {"user_id": 2, "motion_submitter_ids": [2]}
        )
        self.assert_model_exists(
            "meeting_user/2", {"user_id": 3, "motion_submitter_ids": [3]}
        )
        self.assert_model_exists(
            "meeting_user/3", {"user_id": 1, "motion_submitter_ids": [1]}
        )

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

    def test_with_new_duplicate_tags_and_blocks(self) -> None:
        self.json_upload_with_tags_and_blocks()
        self.set_models(
            {
                "tag/7": {"name": "Tag-liatelle", "meeting_id": 42},
                "motion_block/7": {"title": "Blockolade", "meeting_id": 42},
                "meeting/42": {
                    "tag_ids": [1, 2, 3, 4, 7],
                    "motion_block_ids": [1, 2, 3, 4, 7],
                },
            }
        )
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

    def test_update_with_changed_number(self) -> None:
        self.json_upload_simple_update()
        self.set_models({"motion/42": {"number": "CHANGED01"}})
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0]["state"] == ImportState.ERROR
        assert response.json["results"][0][0]["rows"][0]["data"]["number"] == {
            "id": 42,
            "info": ImportState.ERROR,
            "value": "NUM01",
        }
        assert response.json["results"][0][0]["rows"][0]["messages"] == [
            "Error: Motion 42 not found anymore for updating motion 'NUM01'."
        ]

    def test_import_with_newly_duplicate_number(self) -> None:
        self.setup_meeting_with_settings(5, True, True)
        self.set_models(
            {
                "import_preview/55": {
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
                                    "number": {
                                        "info": ImportState.DONE,
                                        "value": "NUM01",
                                    },
                                    "submitters_username": [
                                        {
                                            "value": "admin",
                                            "info": ImportState.GENERATED,
                                            "id": 1,
                                        }
                                    ],
                                    "meeting_id": 5,
                                },
                            }
                        ],
                    },
                }
            }
        )
        response = self.request("motion.import", {"id": 55, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0]["state"] == ImportState.ERROR
        assert response.json["results"][0][0]["rows"][0]["messages"] == [
            "Error: Row state expected to be 'done', but it is 'new'."
        ]
        assert (
            response.json["results"][0][0]["rows"][0]["data"]["number"]["info"]
            == ImportState.ERROR
        )

    def test_import_without_reason_when_required(self) -> None:
        self.setup_meeting_with_settings(5, True, True)
        self.set_models(
            {
                "import_preview/55": {
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
                                    "submitters_username": [
                                        {
                                            "value": "admin",
                                            "info": ImportState.GENERATED,
                                            "id": 1,
                                        }
                                    ],
                                    "meeting_id": 5,
                                },
                            }
                        ],
                    },
                }
            }
        )
        response = self.request("motion.import", {"id": 55, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0]["state"] == ImportState.ERROR
        assert response.json["results"][0][0]["rows"][0]["messages"] == [
            "Error: Reason is required"
        ]
        assert response.json["results"][0][0]["rows"][0]["data"]["reason"] == {
            "value": "",
            "info": ImportState.ERROR,
        }

    def test_update_with_replaced_number(self) -> None:
        self.json_upload_simple_update()
        self.set_models(
            {
                "motion/42": {"number": "CHANGED01"},
                "motion/56": {
                    "meeting_id": 42,
                    "number": "NUM01",
                    "title": "Impostor",
                    "text": "<p>motion</p>",
                },
                "meeting/42": {"motion_ids": [42, 56, 4200]},
            }
        )
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0]["state"] == ImportState.ERROR
        assert response.json["results"][0][0]["rows"][0]["data"]["number"] == {
            "id": 42,
            "info": ImportState.ERROR,
            "value": "NUM01",
        }
        assert response.json["results"][0][0]["rows"][0]["messages"] == [
            "Error: Number 'NUM01' found in different id (56 instead of 42)"
        ]

    def test_update_with_duplicated_number(self) -> None:
        self.json_upload_simple_update()
        self.set_models(
            {
                "motion/56": {
                    "meeting_id": 42,
                    "number": "NUM01",
                    "title": "Impostor",
                    "text": "<p>motion</p>",
                },
                "meeting/42": {"motion_ids": [42, 56, 4200]},
            }
        )
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0]["state"] == ImportState.ERROR
        assert response.json["results"][0][0]["rows"][0]["data"]["number"] == {
            "id": 42,
            "info": ImportState.ERROR,
            "value": "NUM01",
        }
        assert response.json["results"][0][0]["rows"][0]["messages"] == [
            "Error: Number 'NUM01' is duplicated in import."
        ]

    def test_update_with_duplicated_number_2(self) -> None:
        self.setup_meeting_with_settings(5, True, True)
        row = {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "id": 5,
                "title": {
                    "value": "New",
                    "info": ImportState.DONE,
                },
                "text": {
                    "value": "Motion",
                    "info": ImportState.DONE,
                },
                "number": {"value": "NUM01", "info": ImportState.DONE, "id": 5},
                "submitters_username": [
                    {
                        "value": "admin",
                        "info": ImportState.GENERATED,
                        "id": 1,
                    }
                ],
                "meeting_id": 5,
            },
        }
        self.set_models(
            {
                "import_preview/123": {
                    "state": ImportState.DONE,
                    "name": "motion",
                    "result": {
                        "rows": [row, row.copy()],
                    },
                }
            }
        )
        response = self.request("motion.import", {"id": 123, "import": True})
        self.assert_status_code(response, 200)
        for i in range(2):
            assert (
                response.json["results"][0][0]["rows"][i]["state"] == ImportState.ERROR
            )
            assert response.json["results"][0][0]["rows"][i]["data"]["number"] == {
                "id": 5,
                "info": ImportState.ERROR,
                "value": "NUM01",
            }
            assert response.json["results"][0][0]["rows"][i]["messages"] == [
                "Error: Number 'NUM01' is duplicated in import."
            ]

    def test_with_replaced_tags_and_blocks(self) -> None:
        self.json_upload_with_tags_and_blocks()
        self.set_models(
            {
                "tag/1": {"name": "Changed"},
                "tag/7": {"name": "Tag-liatelle", "meeting_id": 42},
                "motion_block/1": {"title": "Changed"},
                "motion_block/7": {"title": "Blockolade", "meeting_id": 42},
                "meeting/42": {
                    "tag_ids": [1, 2, 3, 4, 7],
                    "motion_block_ids": [1, 2, 3, 4, 7],
                },
            }
        )
        response = self.request("motion.import", {"id": 1, "import": True})
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0]["state"] == ImportState.ERROR
        assert response.json["results"][0][0]["rows"][0]["data"]["tags"] == [
            {
                "info": ImportState.ERROR,
                "value": "Tag-liatelle",
            },
            {"id": 2, "info": ImportState.DONE, "value": "Tag-you're-it"},
            {"value": "Tag-ether", "info": "warning"},
            {"value": "Price tag", "info": "warning"},
            {"value": "Not a tag", "info": "warning"},
        ]
        assert response.json["results"][0][0]["rows"][0]["data"]["block"] == {
            "info": ImportState.ERROR,
            "value": "Blockolade",
        }
        assert (
            "Error: Tag search didn't deliver the same result as in the preview: Tag-liatelle"
            in response.json["results"][0][0]["rows"][0]["messages"]
        )
        assert (
            "Error: Motion block search didn't deliver the same result as in the preview"
            in response.json["results"][0][0]["rows"][0]["messages"]
        )

    def test_update_with_broken_id_entries(self) -> None:
        self.setup_meeting_with_settings(5, True, True)
        self.set_models(
            {
                "import_preview/123": {
                    "state": ImportState.DONE,
                    "name": "motion",
                    "result": {
                        "rows": [
                            {
                                "id": 5,
                                "state": ImportState.DONE,
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
                                    "number": {
                                        "value": "NUM01",
                                        "info": ImportState.DONE,
                                        "id": 5,
                                    },
                                    "submitters_username": [
                                        {
                                            "value": "admin",
                                            "info": ImportState.GENERATED,
                                            "id": 1,
                                        }
                                    ],
                                    "meeting_id": 5,
                                },
                            },
                        ],
                    },
                }
            }
        )
        response = self.request("motion.import", {"id": 123, "import": True})
        self.assert_status_code(response, 400)
        assert (
            "Invalid JsonUpload data: A data row with state 'done' must have an 'id'"
            in response.json["message"]
        )

    def test_update_with_broken_id_entries_2(self) -> None:
        self.setup_meeting_with_settings(5, True, True)
        self.set_models(
            {
                "import_preview/123": {
                    "state": ImportState.DONE,
                    "name": "motion",
                    "result": {
                        "rows": [
                            {
                                "state": ImportState.DONE,
                                "messages": [],
                                "data": {
                                    "id": 5,
                                    "title": {
                                        "value": "New",
                                        "info": ImportState.DONE,
                                    },
                                    "text": {
                                        "value": "Motion",
                                        "info": ImportState.DONE,
                                    },
                                    "number": {
                                        "value": "NUM01",
                                        "info": ImportState.DONE,
                                    },
                                    "submitters_username": [
                                        {
                                            "value": "admin",
                                            "info": ImportState.GENERATED,
                                            "id": 1,
                                        }
                                    ],
                                    "meeting_id": 5,
                                },
                            },
                        ],
                    },
                }
            }
        )
        response = self.request("motion.import", {"id": 123, "import": True})
        self.assert_status_code(response, 400)
        assert (
            "Invalid JsonUpload data: A data row with state 'done' must have an 'id'"
            in response.json["message"]
        )
