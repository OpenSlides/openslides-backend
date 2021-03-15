from tests.system.action.base import BaseActionTestCase


class ProjectionUpdate(BaseActionTestCase):
    def test_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "projector/23": {"meeting_id": 1, "current_projection_ids": [33]},
                "projection/33": {"meeting_id": 1, "current_projector_id": 23},
            }
        )
        response = self.request(
            "projection.update",
            {
                "id": 33,
                "current_projector_id": None,
                "history_projector_id": 23,
            },
        )
        self.assert_status_code(response, 200)
        projection = self.get_model("projection/33")
        assert projection.get("current_projector_id") is None
        assert projection.get("history_projector_id") == 23
        projector = self.get_model("projector/23")
        assert projector.get("current_projection_ids") == []
        assert projector.get("history_projection_ids") == [33]
