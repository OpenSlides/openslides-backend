from tests.system.action.base import BaseActionTestCase


class ProjectionUpdate(BaseActionTestCase):
    def test_correct(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "projection/33": {
                    "meeting_id": 1,
                    "current_projector_id": 1,
                    "content_object_id": "meeting/1",
                },
            }
        )
        response = self.request(
            "projection.update",
            {
                "id": 33,
                "current_projector_id": None,
                "history_projector_id": 1,
                "weight": 11,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projection/33",
            {"current_projector_id": None, "history_projector_id": 1, "weight": 11},
        )
        self.assert_model_exists(
            "projector/1",
            {"current_projection_ids": None, "history_projection_ids": [33]},
        )
