from tests.system.action.base import BaseActionTestCase


class MotionUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(
            "motion/111",
            {
                "title": "title_srtgb123",
                "number": "123",
                "text": "<i>test</i>",
                "reason": "<b>test2</b>",
                "modified_final_version": "blablabla",
                "amendment_paragraph_$": ["3"],
                "amendment_paragraph_$3": "testtesttest",
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.update",
                    "data": [
                        {
                            "id": 111,
                            "title": "title_bDFsWtKL",
                            "number": "124",
                            "text": "text_eNPkDVuq",
                            "reason": "reason_ukWqADfE",
                            "modified_final_version": "mfv_ilVvBsUi",
                            "amendment_paragraph_$": {3: "<html>test</html>"},
                            "attachment_ids": [],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model.get("title") == "title_bDFsWtKL"
        assert model.get("number") == "124"
        assert model.get("text") == "text_eNPkDVuq"
        assert model.get("reason") == "reason_ukWqADfE"
        assert model.get("modified_final_version") == "mfv_ilVvBsUi"
        assert model.get("amendment_paragraph_$3") == "&lt;html&gt;test&lt;/html&gt;"
        assert model.get("amendment_paragraph_$") == ["3"]
        assert model.get("attachment_ids") == []

    def test_update_wrong_id(self) -> None:
        self.create_model(
            "motion/111",
            {
                "title": "title_srtgb123",
                "number": "123",
                "text": "<i>test</i>",
                "reason": "<b>test2</b>",
                "modified_final_version": "blablabla",
            },
        )
        response = self.client.post(
            "/",
            json=[{"action": "motion.update", "data": [{"id": 112, "number": "999"}]}],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion/111")
        assert model.get("number") == "123"

    def test_update_text_without_previous(self) -> None:
        self.create_model(
            "motion/111",
            {
                "title": "title_srtgb123",
                "number": "123",
                "reason": "<b>test2</b>",
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.update",
                    "data": [
                        {
                            "id": 111,
                            "title": "title_bDFsWtKL",
                            "number": "124",
                            "text": "text_eNPkDVuq",
                            "reason": "reason_ukWqADfE",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot update text, because it was not set in the old values.",
            response.json["message"],
        )

    def test_update_amendment_paragraphs_without_previous(self) -> None:
        self.create_model(
            "motion/111",
            {
                "title": "title_srtgb123",
                "number": "123",
                "modified_final_version": "blablabla",
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.update",
                    "data": [
                        {
                            "id": 111,
                            "title": "title_bDFsWtKL",
                            "number": "124",
                            "amendment_paragraph_$": {3: "<html>test</html>"},
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot update amendment_paragraph_$, because it was not set in the old values.",
            response.json["message"],
        )

    def test_update_required_reason(self) -> None:
        self.create_model(
            "meeting/77", {"name": "name_TZRIHsSD", "motions_reason_required": True}
        )
        self.create_model(
            "motion/111",
            {
                "title": "title_srtgb123",
                "number": "123",
                "modified_final_version": "blablabla",
                "meeting_id": 77,
                "reason": "balblabla",
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.update",
                    "data": [
                        {
                            "id": 111,
                            "title": "title_bDFsWtKL",
                            "number": "124",
                            "reason": "",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn("Reason is required to update.", response.json["message"])

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
