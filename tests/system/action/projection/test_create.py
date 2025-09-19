from tests.system.action.base import BaseActionTestCase


class ProjectionCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "assignment/1": {
                    "title": "title_srtgb123",
                    "sequential_number": 1,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "projection.create",
            {
                "content_object_id": "assignment/1",
                "current_projector_id": 1,
                "options": {},
                "stable": True,
                "type": "test",
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projection/1",
            {
                "content_object_id": "assignment/1",
                "meeting_id": 1,
                "options": {},
                "stable": True,
                "type": "test",
            },
        )
        self.assert_model_exists("projector/1", {"current_projection_ids": [1]})
        self.assert_model_exists("meeting/1", {"all_projection_ids": [1]})
