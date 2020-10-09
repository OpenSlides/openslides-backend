from tests.system.action.base import BaseActionTestCase


class MotionUpdateMetadataActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model("meeting/2538", {"name": "name_jkPIYjFz"})
        self.create_model("motion/111", {"name": "name_srtgb123", "meeting_id": 2538})
        self.create_model("motion_category/4", {"name": "name_GdPzDztT"})
        self.create_model("motion_block/51", {"title": "title_ddyvpXch"})

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.update_metadata",
                    "data": [
                        {
                            "id": 111,
                            "state_extension": "test_blablab_noon",
                            "recommendation_extension": "ext_sldennt",
                            "category_id": 4,
                            "block_id": 51,
                            "supporter_ids": [],
                            "tag_ids": [],
                            "attachment_ids": [],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model.get("state_extension") == "test_blablab_noon"
        assert model.get("recommendation_extension") == "ext_sldennt"
        assert model.get("category_id") == 4
        assert model.get("block_id") == 51
        assert model.get("supporter_ids") == []
        assert model.get("tag_ids") == []
        assert model.get("attachment_ids") == []

    def test_update_wrong_id(self) -> None:
        self.create_model("motion/111", {"name": "name_srtgb123"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.update_metadata",
                    "data": [{"id": 112, "state_extension": "ext_Xcdfgee"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion/111")
        assert model.get("name") == "name_srtgb123"
        assert model.get("state_extension") is None
