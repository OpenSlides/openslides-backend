from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorControlView(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models({"projector/1": {"scale": 11, "scroll": 13, "meeting_id": 1}})

    def test_reset(self) -> None:
        response = self.request(
            "projector.control_view", {"id": 1, "field": "scale", "direction": "reset"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("projector/1", {"scale": 0, "scroll": 13})

    def test_up(self) -> None:
        response = self.request(
            "projector.control_view",
            {"id": 1, "field": "scroll", "direction": "up", "step": 7},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("projector/1", {"scale": 11, "scroll": 20})

    def test_down(self) -> None:
        response = self.request(
            "projector.control_view",
            {"id": 1, "field": "scale", "direction": "down"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("projector/1", {"scale": 10, "scroll": 13})

    def test_wrong_direction(self) -> None:
        response = self.request(
            "projector.control_view",
            {"id": 1, "field": "scale", "direction": "invalid"},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action projector.control_view: data.direction must be one of ['up', 'down', 'reset']",
            response.json["message"],
        )

    def test_wrong_step(self) -> None:
        response = self.request(
            "projector.control_view",
            {"id": 1, "field": "scale", "direction": "up", "step": 0},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action projector.control_view: data.step must be bigger than or equal to 1",
            response.json["message"],
        )

    def test_control_view_scroll_min(self) -> None:
        response = self.request(
            "projector.control_view",
            {"id": 1, "field": "scroll", "direction": "down", "step": 100},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("projector/1", {"scale": 11, "scroll": 0})

    def test_control_view_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.control_view",
            {"id": 1, "field": "scale", "direction": "reset"},
        )

    def test_control_view_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.control_view",
            {"id": 1, "field": "scale", "direction": "reset"},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_control_view_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector.control_view",
            {"id": 1, "field": "scale", "direction": "reset"},
        )
