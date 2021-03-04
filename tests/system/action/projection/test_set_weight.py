from tests.system.action.base import BaseActionTestCase


class ProjectionSetWeight(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "projector/34": {"current_projection_ids": [11]},
                "projection/11": {"current_projector_id": 34, "weight": 100},
            }
        )

    def test_set_weight(self) -> None:
        response = self.request("projection.set_weight", {"id": 11, "weight": 200})
        self.assert_status_code(response, 200)
        projection = self.get_model("projection/11")
        assert projection.get("weight") == 200
