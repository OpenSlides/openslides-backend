from tests.system.action.base import BaseActionTestCase


class MotionCreateAmendmentActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        # create parent motion and workflow
        self.set_models(
            {
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {"name": "name_state34", "meeting_id": 222},
                "motion/1": {
                    "title": "title_eJveLQIh",
                    "sort_child_ids": [],
                    "meeting_id": 222,
                },
            }
        )

    def test_create_amendment(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1},
                "user/1": {"meeting_ids": [222]},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "lead_motion_id": 1,
                "text": "text_test1",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/2")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("lead_motion_id") == 1
        assert model.get("text") == "text_test1"

    def test_create_amendment_default_workflow(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "motions_default_amendment_workflow_id": 12,
                    "is_active_in_organization_id": 1,
                },
                "user/1": {"meeting_ids": [222]},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "lead_motion_id": 1,
                "text": "text_test1",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/2")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("lead_motion_id") == 1
        assert model.get("text") == "text_test1"
        assert model.get("state_id") == 34

    def test_create_with_amendment_paragraphs_valid(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1},
                "user/1": {"meeting_ids": [222]},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "lead_motion_id": 1,
                "amendment_paragraphs": {4: "text"},
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/2")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("lead_motion_id") == 1
        assert model.get("state_id") == 34
        assert model.get("amendment_paragraphs") == {"4": "text"}

    def test_create_with_amendment_paragraphs_0(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1},
                "user/1": {"meeting_ids": [222]},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "lead_motion_id": 1,
                "amendment_paragraphs": {0: "text"},
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/2")
        assert model.get("amendment_paragraphs") == {"0": "text"}

    def test_create_with_amendment_paragraphs_string(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1},
                "user/1": {"meeting_ids": [222]},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "lead_motion_id": 1,
                "amendment_paragraphs": {"0": "text"},
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/2")
        assert model.get("amendment_paragraphs") == {"0": "text"}

    def test_create_with_amendment_paragraphs_invalid(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1},
                "user/1": {"meeting_ids": [222]},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "lead_motion_id": 1,
                "amendment_paragraphs": {"a4": "text"},
            },
        )
        self.assert_status_code(response, 400)
        assert "data.amendment_paragraphs must not contain {'a4'} properties" in str(
            response.json["message"]
        )

    def test_create_with_amendment_paragraphs_invalid_2(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1},
                "user/1": {"meeting_ids": [222]},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "lead_motion_id": 1,
                "amendment_paragraphs": ["test"],
            },
        )
        self.assert_status_code(response, 400)
        assert "data.amendment_paragraphs must be object" in response.json["message"]

    def test_create_with_amendment_paragraphs_html(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1},
                "user/1": {"meeting_ids": [222]},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "lead_motion_id": 1,
                "amendment_paragraphs": {
                    "0": "<it>test</it>",
                    "1": "</><</>broken>",
                },
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2",
            {
                "amendment_paragraphs": {
                    "0": "&lt;it&gt;test&lt;/it&gt;",
                    "1": "&lt;broken&gt;",
                }
            },
        )

    def test_create_missing_text(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1},
                "user/1": {"meeting_ids": [222]},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        assert "Text or amendment_paragraphs is required in this context." in str(
            response.json["message"]
        )

    def test_create_text_and_amendment_paragraphs(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1},
                "user/1": {"meeting_ids": [222]},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "lead_motion_id": 1,
                "text": "text",
                "amendment_paragraphs": {4: "text"},
            },
        )
        self.assert_status_code(response, 400)
        assert "give both of text and amendment_paragraphs" in response.json["message"]

    def test_create_missing_reason(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "motions_reason_required": True,
                    "is_active_in_organization_id": 1,
                },
                "user/1": {"meeting_ids": [222]},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "text",
            },
        )
        self.assert_status_code(response, 400)
        assert "Reason is required" in response.json["message"]
