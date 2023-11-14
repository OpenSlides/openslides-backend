from .test_json_upload import MotionImportTestMixin


class MotionJsonUpload(MotionImportTestMixin):
    def setUp(self) -> None:
        super().setUp()
        base_meeting_id = 42
        base_motion_id = 100
        base_block_id = 1000
        base_tag_id = 10000
        (settings, users) = self.get_base_user_and_meeting_settings(
            base_meeting_id, base_motion_id
        )  # what about set number and reason required?
        settings = {
            meeting_id: self.extend_meeting_setting_with_blocks(
                self.extend_meeting_setting_with_tags(
                    self.extend_meeting_setting_with_categories(
                        settings[meeting_id], categories={}, motion_to_category_ids={}
                    ),
                    base_tag_id,
                    extra_tags=[],
                ),
                base_block_id,
                extra_blocks=[],
            )
            for meeting_id in settings
        }
        # TODO: Add import_previews and then set_model

    # -------------------------------------------------------
    # --------------------[ Basic tests ]--------------------
    # -------------------------------------------------------

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
