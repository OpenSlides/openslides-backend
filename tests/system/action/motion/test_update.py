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
                "amendment_paragraph_$": '["3"]',
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
                            "amendment_paragraphs": {"3": "<html>test</html>"},
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
        assert model.get("amendment_paragraph_$") == '["3"]'

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
            str(response.data),
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
                            "amendment_paragraphs": {3: "<html>test</html>"},
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot update amendment_paragraphs, because it was not set in the old values.",
            str(response.data),
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
        self.assertIn("Reason is required to update.", str(response.data))
