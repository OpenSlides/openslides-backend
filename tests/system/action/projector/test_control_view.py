from tests.system.action.base import BaseActionTestCase


class ProjectorControlView(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models({"projector/1": {"scale": 11, "scroll": 13}})

    def test_reset(self) -> None:
        response = self.request(
            "projector.control_view", {"id": 1, "field": "scale", "direction": "reset"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("projector/1")
        assert model.get("scale") == 0
        assert model.get("scroll") == 13

    def test_up(self) -> None:
        response = self.request(
            "projector.control_view",
            {"id": 1, "field": "scroll", "direction": "up", "step": 7},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("projector/1")
        assert model.get("scale") == 11
        assert model.get("scroll") == 20

    def test_down(self) -> None:
        response = self.request(
            "projector.control_view",
            {"id": 1, "field": "scale", "direction": "down"},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("projector/1")
        assert model.get("scale") == 10
        assert model.get("scroll") == 13

    def test_wrong_direction(self) -> None:
        response = self.request(
            "projector.control_view",
            {"id": 1, "field": "scale", "direction": "invalid"},
        )
        self.assert_status_code(response, 400)
        assert (
            "data.direction must be one of ['up', 'down', 'reset']"
            in response.data.decode()
        )

    def test_wrong_step(self) -> None:
        response = self.request(
            "projector.control_view",
            {"id": 1, "field": "scale", "direction": "up", "step": 0},
        )
        self.assert_status_code(response, 400)
        assert "data.step must be bigger than or equal to 1" in response.data.decode()
