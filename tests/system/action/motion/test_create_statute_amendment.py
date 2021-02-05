from tests.system.action.base import BaseActionTestCase


class MotionCreateAmendmentActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        # create parent paragraph and workflow
        self.create_model(
            "motion_workflow/12",
            {"name": "name_workflow1", "first_state_id": 34, "state_ids": [34]},
        )
        self.create_model(
            "motion_state/34", {"name": "name_state34", "meeting_id": 222}
        )
        self.create_model(
            "motion_statute_paragraph/1",
            {"title": "title_eJveLQIh", "meeting_id": 222},
        )

    def test_create_statute_amendment(self) -> None:
        self.create_model("meeting/222", {})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 222,
                            "workflow_id": 12,
                            "statute_paragraph_id": 1,
                            "text": "text",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("statute_paragraph_id") == 1
        assert model.get("text") == "text"

    def test_create_statute_amendment_default_workflow(self) -> None:
        self.create_model(
            "meeting/222", {"motions_default_statute_amendment_workflow_id": 12}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 222,
                            "statute_paragraph_id": 1,
                            "text": "text",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("statute_paragraph_id") == 1
        assert model.get("text") == "text"
        assert model.get("state_id") == 34

    def test_create_with_amendment_paragraphs(self) -> None:
        self.create_model("meeting/222", {})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 222,
                            "statute_paragraph_id": 1,
                            "text": "text",
                            "amendment_paragraphs": {"4": "text"},
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "give amendment_paragraphs in this context" in response.json.get(
            "message", ""
        )

    def test_create_reason_missing(self) -> None:
        self.create_model("meeting/222", {"motions_reason_required": True})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 222,
                            "statute_paragraph_id": 1,
                            "text": "text",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Reason is required" in response.json["message"]
