from typing import Any, Dict, List

from openslides_backend.action.mixins.import_mixins import ImportState

from .test_json_upload import MotionImportTestMixin


class MotionJsonUpload(MotionImportTestMixin):
    def set_up_models_with_import_previews_and_get_next_motion_id(
        self,
        additional_data: List[Dict[str, Any]] = [{}],
        base_meeting_id: int = 42,
        base_motion_id: int = 100,
        base_block_id: int = 1000,
        base_tag_id: int = 10000,
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> int:
        (settings, users) = self.get_base_user_and_meeting_settings(
            base_meeting_id, base_motion_id, is_reason_required, is_set_number
        )
        settings = {
            base_meeting_id: self.extend_meeting_setting_with_blocks(
                self.extend_meeting_setting_with_tags(
                    self.extend_meeting_setting_with_categories(
                        settings[base_meeting_id],
                        categories={
                            400: {"name": "Category A", "prefix": "A"},
                            401: {"name": "Category B", "prefix": "B"},
                            403: {"name": "Copygory", "prefix": "COPY"},
                            404: {"name": "Copygory", "prefix": "COPY"},
                            405: {"name": "Copygory", "prefix": "KOPIE"},
                            406: {"name": "Weak Copygory", "prefix": "COPY"},
                            407: {"name": "No prefix"},
                        },
                        motion_to_category_ids={
                            base_motion_id: 407,
                            (base_motion_id + 1): 400,
                            (base_motion_id + 2): 401,
                            (base_motion_id + 3): 403,
                            (base_motion_id + 4): 405,
                        },
                    ),
                    base_tag_id,
                    extra_tags=["Got tag go"],
                    motion_to_tag_ids={
                        (base_motion_id + i): [base_tag_id] for i in range(5)
                    },
                ),
                base_block_id,
                extra_blocks=["Block and roll"],
                motion_to_block_ids={
                    (base_motion_id + i): base_block_id for i in range(5)
                },
            ),
            (base_meeting_id + 1): self.extend_meeting_setting_with_blocks(
                self.extend_meeting_setting_with_tags(
                    self.extend_meeting_setting_with_categories(
                        settings[base_meeting_id + 1],
                        categories={
                            801: {"name": "Category B", "prefix": "B"},
                            802: {"name": "Category C", "prefix": "C"},
                        },
                        motion_to_category_ids={
                            base_motion_id * 2: 801,
                            (base_motion_id * 2 + 1): 802,
                        },
                    ),
                    base_tag_id * 2,
                    extra_tags=["rag-tag"],
                    motion_to_tag_ids={},
                ),
                base_block_id * 2,
                extra_blocks=["Blocked"],
                motion_to_block_ids={(base_motion_id * 2): (base_block_id * 2)},
            ),
        }
        model_data = {
            **self.set_up_models(settings, users),
            "import_preview/2": {
                "state": ImportState.DONE,
                "name": "motion",
                "result": {
                    "rows": [
                        {
                            "state": ImportState.DONE
                            if date.get("id")
                            else ImportState.NEW,
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
                                **date,
                                "meeting_id": base_meeting_id,
                            },
                        }
                        for date in additional_data
                    ],
                },
            },
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
                                "meeting_id": base_meeting_id,
                            },
                        },
                    ],
                },
            },
        }
        self.set_models(model_data)
        return base_motion_id + 105

    # -------------------------------------------------------
    # --------------------[ Basic tests ]--------------------
    # -------------------------------------------------------

    def assert_simple_import(
        self,
        response: Any,
        motion_id: int,
        row_data: Dict[str, Any],
        submitter_user_id_to_weight: Dict[int, int] = {1: 1},
    ) -> None:
        self.assert_status_code(response, 200)
        motion = self.assert_model_exists(
            f"motion/{motion_id}",
            row_data,
        )
        assert len(motion.get("submitter_ids", [])) == len(
            submitter_user_id_to_weight.keys()
        )
        submitter_ids = motion.get("submitter_ids", [])
        submitter_user_id_to_weight_tuple_list = list(
            submitter_user_id_to_weight.items()
        )
        for i in range(len(submitter_ids)):
            submitter_id = submitter_ids[i]
            (
                submitter_user_id,
                submitter_weight,
            ) = submitter_user_id_to_weight_tuple_list[i]
            submitter = self.assert_model_exists(
                f"motion_submitter/{submitter_id}",
                {"meeting_id": 42, "motion_id": motion_id, "weight": submitter_weight},
            )
            assert (meeting_user_id := submitter.get("meeting_user_id"))
            self.assert_model_exists(
                f"meeting_user/{meeting_user_id}",
                {"meeting_id": 42, "user_id": submitter_user_id},
            )
        self.assert_model_not_exists("import_preview/2")

    def test_import_create_simple(self) -> None:
        next_id = self.set_up_models_with_import_previews_and_get_next_motion_id()
        response = self.request("motion.import", {"id": 2, "import": True})
        self.assert_simple_import(response, next_id, {"title": "New", "text": "Motion"})

    def test_import_update_simple(self) -> None:
        self.set_up_models_with_import_previews_and_get_next_motion_id(
            [
                {
                    "number": {"info": ImportState.DONE, "id": 101, "value": "NUM01"},
                    "id": 101,
                }
            ]
        )
        self.assert_model_exists(
            "motion/101",
            {
                "number": "NUM01",
                "category_id": 400,
                "block_id": 1000,
                "tag_ids": [10000],
                "submitter_ids": [70000],
            },
        )
        response = self.request("motion.import", {"id": 2, "import": True})
        self.assert_simple_import(
            response,
            101,
            {
                "title": "New",
                "text": "Motion",
                "number": "NUM01",
                "category_id": None,
                "block_id": None,
                "tag_ids": [],
                "submitter_ids": [150101],
            },
        )

    def test_import_update_simple_2(self) -> None:
        self.set_up_models_with_import_previews_and_get_next_motion_id(
            [
                {
                    "number": {
                        "info": ImportState.DONE,
                        "id": 102,
                        "value": "AMNDMNT1",
                    },
                    "text": {"info": ImportState.DONE, "value": ""},
                    "id": 102,
                }
            ]
        )
        self.assert_model_exists(
            "motion/102", {"number": "AMNDMNT1", "supporter_meeting_user_ids": [700]}
        )
        response = self.request("motion.import", {"id": 2, "import": True})
        self.assert_simple_import(
            response,
            102,
            {
                "title": "New",
                "text": "",
                "number": "AMNDMNT1",
                "supporter_meeting_user_ids": [],
            },
        )

    def prepare_complex_test(
        self, changed_entries: Dict[str, Any] = {}, is_update: bool = False
    ) -> int:
        data = {
            "number": {"info": ImportState.DONE, "value": "DUM01"},
            "title": {"info": ImportState.DONE, "value": "Always look on..."},
            "text": {
                "info": ImportState.DONE,
                "value": "...the bright side...",
            },
            "reason": {"info": ImportState.DONE, "value": "...of life!"},
            "category_name": {
                "info": ImportState.DONE,
                "id": 401,
                "value": "Category B",
            },
            "category_prefix": "B",
            "block": {
                "info": ImportState.DONE,
                "id": 1001,
                "value": "Blockodile",
            },
            "submitters_username": [
                {"info": ImportState.DONE, "id": 3, "value": "firstMeeting"},
                {"info": ImportState.DONE, "id": 12, "value": "multiMeeting"},
                {
                    "info": ImportState.DONE,
                    "id": 7,
                    "value": "firstMeetingBoth",
                },
                {
                    "info": ImportState.DONE,
                    "id": 4,
                    "value": "firstMeetingSubmitter",
                },
            ],
            "supporters_username": [
                {
                    "info": ImportState.DONE,
                    "id": 13,
                    "value": "multiMeetingSubmitter",
                },
                {
                    "info": ImportState.DONE,
                    "id": 6,
                    "value": "firstMeetingSupporter",
                },
            ],
            "tags": [
                {"info": ImportState.DONE, "id": 10003, "value": "Tag-ether"},
                {"info": ImportState.DONE, "id": 10002, "value": "Price tag"},
            ],
        }
        if is_update:
            data.update(
                {
                    "id": 101,
                    "number": {"info": ImportState.DONE, "id": 101, "value": "NUM01"},
                }
            )
        for key in changed_entries:
            data[key] = changed_entries[key]
        return self.set_up_models_with_import_previews_and_get_next_motion_id([data])

    def test_import_update_complex(self) -> None:
        self.prepare_complex_test(is_update=True)
        response = self.request("motion.import", {"id": 2, "import": True})
        self.assert_simple_import(
            response,
            101,
            {
                "title": "Always look on...",
                "text": "...the bright side...",
                "reason": "...of life!",
                "number": "NUM01",
                "category_id": 401,
                "block_id": 1001,
                "submitter_ids": [70000, 150101, 150102, 150103],
                "supporter_meeting_user_ids": [1300, 600],
                "tag_ids": [10003, 10002],
            },
            {7: 3, 3: 1, 12: 2, 4: 4},
        )

    def test_import_create_complex(self) -> None:
        next_id = self.prepare_complex_test()
        response = self.request("motion.import", {"id": 2, "import": True})
        self.assert_simple_import(
            response,
            next_id,
            {
                "title": "Always look on...",
                "text": "...the bright side...",
                "reason": "...of life!",
                "number": "DUM01",
                "category_id": 401,
                "block_id": 1001,
                "submitter_ids": [150101, 150102, 150103, 150104],
                "supporter_meeting_user_ids": [1300, 600],
                "tag_ids": [10003, 10002],
            },
            {3: 1, 12: 2, 7: 3, 4: 4},
        )

    def assert_error_for_changed_property(
        self, response: Any, changed_keys: List[str], error_messages: list[str]
    ) -> None:
        assert response.json["results"][0][0]["state"] == ImportState.ERROR
        errors = response.json["results"][0][0]["rows"][0]["messages"]
        for message in error_messages:
            assert message in errors
        assert len(errors) == len(error_messages)
        data = response.json["results"][0][0]["rows"][0]["data"]
        for key in data:
            if key in changed_keys:
                if isinstance(data[key], Dict):
                    assert data[key]["info"] == ImportState.ERROR
                elif isinstance(data[key], List):
                    assert ImportState.ERROR in [date["info"] for date in data[key]]
            elif isinstance(data[key], Dict):
                assert data[key]["info"] != ImportState.ERROR
            elif isinstance(data[key], List):
                assert ImportState.ERROR not in [date["info"] for date in data[key]]

    def test_import_update_changed_number_name(self) -> None:
        self.prepare_complex_test(
            {
                "number": {
                    "id": 101,
                    "info": ImportState.DONE,
                    "value": "This shouldn't be found",
                }
            },
            is_update=True,
        )
        response = self.request("motion.import", {"id": 2, "import": True})
        self.assert_error_for_changed_property(
            response,
            ["number"],
            ["Error: TODO"],
        )

    def assert_changed_submitter_name(self, is_update: bool = False) -> None:
        self.prepare_complex_test(
            {
                "submitters_username": [
                    {
                        "id": 7,
                        "info": ImportState.DONE,
                        "value": "updatedUser",
                    }
                ]
            },
            is_update,
        )
        response = self.request("motion.import", {"id": 2, "import": True})
        self.assert_error_for_changed_property(
            response,
            ["submitters_username"],
            ["Error: TODO"],
        )

    def test_import_create_changed_submitter_name(self) -> None:
        self.assert_changed_submitter_name()

    def test_import_update_changed_submitter_name(self) -> None:
        self.assert_changed_submitter_name(True)

    def test_import_create_simple_with_reason_required(self) -> None:
        self.set_up_models_with_import_previews_and_get_next_motion_id(
            is_reason_required=True
        )
        response = self.request("motion.import", {"id": 2, "import": True})
        self.assert_status_code(response, 400)
        assert response.json["message"] == "Reason is required"

    def test_import_update_simple_with_reason_required(self) -> None:
        self.set_up_models_with_import_previews_and_get_next_motion_id(
            [
                {
                    "number": {"info": ImportState.DONE, "id": 101, "value": "NUM01"},
                    "id": 101,
                }
            ],
            is_reason_required=True,
        )
        response = self.request("motion.import", {"id": 2, "import": True})
        self.assert_status_code(response, 400)
        assert response.json["message"] == "Reason is required to update."

    def test_import_abort(self) -> None:
        next_id = self.set_up_models_with_import_previews_and_get_next_motion_id()
        response = self.request("motion.import", {"id": 2, "import": False})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("import_preview/2")
        self.assert_model_not_exists(f"motion/{next_id}")

    def test_import_wrong_import_preview(self) -> None:
        self.set_up_models_with_import_previews_and_get_next_motion_id()
        response = self.request("motion.import", {"id": 3, "import": True})
        self.assert_status_code(response, 400)
        assert "Import data cannot be found." in response.json["message"]

    def test_import_wrong_meeting_model_import_preview(self) -> None:
        self.set_up_models_with_import_previews_and_get_next_motion_id()
        response = self.request("motion.import", {"id": 4, "import": True})
        self.assert_status_code(response, 400)
        assert "Import data cannot be found." in response.json["message"]

    # -------------------------------------------------------
    # ---------------[ Test with categories ]----------------
    # -------------------------------------------------------

    # def assert_import_with_category(self, response: Any, motion_id: int, row_data: Dict[str, str])-> None:
    #     self.assert_status_code(response, 200)
    #     user = self.assert_model_exists(
    #         f"motion/{motion_id}",
    #         row_data,
    #     )
    #     assert len(user.get("submitter_ids", [])) == 1
    #     submitter_id = user.get("submitter_ids", [])[0]
    #     submitter = self.assert_model_exists(
    #         f"motion_submitter/{submitter_id}",
    #         {"meeting_id": 42, "motion_id": motion_id},
    #     )
    #     assert (meeting_user_id := submitter.get("meeting_user_id"))
    #     submitter = self.assert_model_exists(
    #         f"meeting_user/{meeting_user_id}",
    #         {"meeting_id": 42, "user_id": 1},
    #     )
    #     self.assert_model_not_exists("import_preview/2")

    # def test_import_create_with_category(self) -> None:
    #     next_id = self.set_up_models_with_import_previews_and_get_next_motion_id()
    #     response = self.request("motion.import", {"id": 2, "import": True})
    #     self.assert_import_with_category(response, next_id, {"title": "New", "text": "Motion"})

    # def test_import_update_with_category(self) -> None:
    #     self.set_up_models_with_import_previews_and_get_next_motion_id(
    #         [
    #             {
    #                 "number": {"info": ImportState.DONE, "id": 101, "value": "NUM01"},
    #                 "id": 101,
    #             }
    #         ]
    #     )
    #     response = self.request("motion.import", {"id": 2, "import": True})
    #     self.assert_import_with_category(response, 101, {"title": "New", "text": "Motion", "number": "NUM01"})

    # -------------------------------------------------------
    # ------------------[ Test with users ]------------------
    # -------------------------------------------------------

    # TODO: Are submitters sorted?

    # -------------------------------------------------------
    # ------------------[ Test with tags ]-------------------
    # -------------------------------------------------------

    # -------------------------------------------------------
    # ------------------[ Test with block ]------------------
    # -------------------------------------------------------
