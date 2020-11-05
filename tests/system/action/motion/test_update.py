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
                            "amendment_paragraphs": {3: "<html>test</html>"},
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
