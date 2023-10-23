from openslides_backend.action.mixins.import_mixins import ImportState
from tests.system.action.base import BaseActionTestCase


class MotionJsonUpload(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/42": {
                    "name": "test",
                    "is_active_in_organization_id": 1,
                    "motions_default_workflow_id": 2,
                },
                "motion_workflow/2": {
                    "state_ids": [2, 3, 4, 5],
                    "first_state_id": 2,
                    "default_workflow_meeting_id": 42,
                },
                "motion_state/2": {},
            }
        )

    def test_json_upload_simple(self) -> None:
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "text": "my", "reason": "stuff"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "meeting_id": 42,
                "title": {"value": "test", "info": ImportState.DONE},
                "text": {"value": "<p>my</p>", "info": ImportState.DONE},
                "reason": {"value": "stuff", "info": ImportState.DONE},
                "submitter_usernames": [
                    {"id": 1, "info": "generated", "value": "admin"}
                ],
            },
        }

    def test_json_upload_empty_data(self) -> None:
        response = self.request(
            "motion.json_upload",
            {"data": [], "meeting_id": 42},
        )
        self.assert_status_code(response, 400)
        assert "data.data must contain at least 1 items" in response.json["message"]

    def test_json_upload_create_missing_title(self) -> None:
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"text": "my", "reason": "stuff"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 400)
        assert "Error: Title is required" in response.json["message"]

    def test_json_upload_create_missing_text(self) -> None:
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "reason": "stuff"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Error: Text or amendment_paragraphs is required in this context."
            in response.json["message"]
        )

    def test_json_upload_create_missing_reason(self) -> None:
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "text": "my"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "meeting_id": 42,
                "title": {"value": "test", "info": ImportState.DONE},
                "text": {"value": "<p>my</p>", "info": ImportState.DONE},
                "submitter_usernames": [
                    {"id": 1, "info": "generated", "value": "admin"}
                ],
            },
        }
