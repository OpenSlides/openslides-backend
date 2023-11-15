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
                        categories={},
                        motion_to_category_ids={},
                    ),
                    base_tag_id,
                    extra_tags=[],
                ),
                base_block_id,
                extra_blocks=[],
            ),
            (base_meeting_id + 1): self.extend_meeting_setting_with_blocks(
                self.extend_meeting_setting_with_tags(
                    self.extend_meeting_setting_with_categories(
                        settings[base_meeting_id + 1],
                        categories={},
                        motion_to_category_ids={},
                    ),
                    base_tag_id * 2,
                    extra_tags=[],
                ),
                base_block_id * 2,
                extra_blocks=[],
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
                                "submitters_username": [
                                    {
                                        "value": "admin",
                                        "info": ImportState.GENERATED,
                                        "id": 1,
                                    }
                                ],
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

    def test_import_create_simple(self) -> None:
        next_id = self.set_up_models_with_import_previews_and_get_next_motion_id()
        response = self.request("motion.import", {"id": 2, "import": True})
        self.assert_status_code(response, 200)
        user = self.assert_model_exists(
            f"motion/{next_id}",
            {"title": "New", "text": "Motion"},
        )
        assert len(user.get("submitter_ids", [])) == 1
        submitter_id = user.get("submitter_ids", [])[0]
        submitter = self.assert_model_exists(
            f"motion_submitter/{submitter_id}",
            {"meeting_id": 42, "motion_id": next_id},
        )
        assert (meeting_user_id := submitter.get("meeting_user_id"))
        submitter = self.assert_model_exists(
            f"meeting_user/{meeting_user_id}",
            {"meeting_id": 42, "user_id": 1},
        )
        self.assert_model_not_exists("import_preview/2")

    def test_import_update_simple(self) -> None:
        self.set_up_models_with_import_previews_and_get_next_motion_id(
            [
                {
                    "number": {"info": ImportState.DONE, "id": 101, "value": "NUM01"},
                    "id": 101,
                }
            ]
        )
        response = self.request("motion.import", {"id": 2, "import": True})
        self.assert_status_code(response, 200)
        user = self.assert_model_exists(
            f"motion/{101}",
            {"title": "New", "text": "Motion"},
        )
        assert len(user.get("submitter_ids", [])) == 1
        submitter_id = user.get("submitter_ids", [])[0]
        submitter = self.assert_model_exists(
            f"motion_submitter/{submitter_id}",
            {"meeting_id": 42, "motion_id": 101},
        )
        assert (meeting_user_id := submitter.get("meeting_user_id"))
        submitter = self.assert_model_exists(
            f"meeting_user/{meeting_user_id}",
            {"meeting_id": 42, "user_id": 1},
        )
        self.assert_model_not_exists("import_preview/2")

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

    # -------------------------------------------------------
    # ------------------[ Test with users ]------------------
    # -------------------------------------------------------

    # -------------------------------------------------------
    # ------------------[ Test with tags ]-------------------
    # -------------------------------------------------------

    # -------------------------------------------------------
    # ------------------[ Test with block ]------------------
    # -------------------------------------------------------
