from tests.system.action.base import BaseActionTestCase


class MotionUpdateMetadataActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model("meeting/2538", {"name": "name_jkPIYjFz"})
        self.create_model(
            "motion/111",
            {
                "meeting_id": 2538,
            },
        )
        self.create_model(
            "motion_category/4",
            {"meeting_id": 2538, "name": "name_GdPzDztT", "motion_ids": []},
        )
        self.create_model(
            "motion_block/51",
            {"meeting_id": 2538, "title": "title_ddyvpXch", "motion_ids": []},
        )
        self.create_model(
            "motion/112",
            {
                "meeting_id": 2538,
            },
        )

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.update_metadata",
                    "data": [
                        {
                            "id": 111,
                            "state_extension": "test_blablab_noon",
                            "recommendation_extension": "ext_sldennt [motion/112]",
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
        assert model.get("recommendation_extension") == "ext_sldennt [motion/112]"
        assert model.get("category_id") == 4
        assert model.get("block_id") == 51
        assert model.get("supporter_ids") == []
        assert model.get("tag_ids") == []
        assert model.get("attachment_ids") == []
        assert model.get("recommendation_extension_reference_ids") == ["motion/112"]

    def test_update_metadata_workflow_id(self) -> None:
        self.create_model("meeting/2538", {"name": "name_jkPIYjFz"})
        self.create_model(
            "motion/111",
            {
                "meeting_id": 2538,
                "state_id": 88,
                "recommendation_id": 88,
            },
        )
        self.create_model(
            "motion_workflow/22", {"name": "name_workflow_22", "meeting_id": 2538}
        )
        self.create_model(
            "motion_state/88",
            {
                "name": "name_blaglup",
                "meeting_id": 2538,
                "workflow_id": 22,
                "motion_ids": [111],
                "motion_recommendation_ids": [111],
            },
        )
        self.create_model(
            "motion_state/23",
            {"name": "name_state_23", "meeting_id": 2538, "motion_ids": []},
        )
        self.create_model(
            "motion_workflow/35",
            {"name": "name_workflow_35", "first_state_id": 23, "meeting_id": 2538},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.update_metadata",
                    "data": [{"id": 111, "workflow_id": 35}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model.get("state_id") == 23
        assert model.get("recommendation_id") is None

    def test_update_metadata_workflow_id_no_change(self) -> None:
        self.create_model("meeting/2538", {"name": "name_jkPIYjFz"})
        self.create_model(
            "motion/111",
            {
                "meeting_id": 2538,
                "state_id": 88,
                "recommendation_id": 88,
            },
        )
        self.create_model(
            "motion_workflow/22", {"name": "name_workflow_22", "meeting_id": 2538}
        )
        self.create_model(
            "motion_state/88",
            {
                "name": "name_blaglup",
                "meeting_id": 2538,
                "workflow_id": 22,
                "motion_ids": [111],
                "motion_recommendation_ids": [111],
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.update_metadata",
                    "data": [{"id": 111, "workflow_id": 22}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model.get("state_id") == 88
        assert model.get("recommendation_id") == 88

    def test_update_wrong_id(self) -> None:
        self.create_model("motion/111", {})
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
        assert model.get("state_extension") is None

    def test_update_metadata_missing_motion(self) -> None:
        self.create_model("meeting/2538", {"name": "name_jkPIYjFz"})
        self.create_model("motion/111", {"meeting_id": 2538})
        self.create_model(
            "motion_category/4", {"name": "name_GdPzDztT", "meeting_id": 2538}
        )
        self.create_model(
            "motion_block/51", {"title": "title_ddyvpXch", "meeting_id": 2538}
        )

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.update_metadata",
                    "data": [
                        {
                            "id": 111,
                            "state_extension": "test_blablab_noon",
                            "recommendation_extension": "ext_sldennt [motion/112]",
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
        assert model.get("recommendation_extension_reference_ids") == []

    def test_meeting_missmatch(self) -> None:
        self.create_model("meeting/1", {"name": "name_GDZvcjPK"})
        self.create_model("meeting/2", {"name": "name_Rwvrqaqj"})
        self.create_model("motion/1", {"meeting_id": 1})
        self.create_model("motion/2", {"meeting_id": 2})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.update_metadata",
                    "data": [
                        {
                            "id": 1,
                            "recommendation_extension": "blablabla [motion/2] blablabla",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "requires the following fields to be equal" in response.data.decode()

    def test_only_motion_allowed(self) -> None:
        self.create_model("meeting/1", {"name": "name_uZXBoHMp"})
        self.create_model("motion/1", {"meeting_id": 1})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.update_metadata",
                    "data": [
                        {
                            "id": 1,
                            "recommendation_extension": "blablabla [assignment/1] blablabla",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Found assignment/1 but only motion is allowed." in str(response.data)
