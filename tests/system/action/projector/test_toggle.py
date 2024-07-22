from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorToggle(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "projector/23": {"meeting_id": 1, "current_projection_ids": []},
            "poll/788": {"meeting_id": 1},
        }

    def setup_models(self, stable: bool) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "projector/23": {"meeting_id": 1, "current_projection_ids": [33]},
                "projection/33": {
                    "meeting_id": 1,
                    "content_object_id": "poll/788",
                    "current_projector_id": 23,
                    "stable": stable,
                },
                "poll/788": {"meeting_id": 1},
            }
        )

    def test_correct_remove_stable_projection(self) -> None:
        self.setup_models(True)
        response = self.request(
            "projector.toggle",
            {
                "ids": [23],
                "content_object_id": "poll/788",
                "meeting_id": 1,
                "stable": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("projection/33")
        projector = self.get_model("projector/23")
        assert projector.get("current_projection_ids") == []

    def test_correct_remove_unstable_projection(self) -> None:
        self.setup_models(False)
        response = self.request(
            "projector.toggle",
            {
                "ids": [23],
                "content_object_id": "poll/788",
                "meeting_id": 1,
                "stable": False,
            },
        )
        self.assert_status_code(response, 200)
        projector = self.get_model("projector/23")
        assert projector.get("history_projection_ids") == [33]

    def test_correct_add_projection(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "projector/23": {"meeting_id": 1, "current_projection_ids": []},
                "poll/788": {"meeting_id": 1},
            }
        )
        response = self.request(
            "projector.toggle",
            {
                "ids": [23],
                "content_object_id": "poll/788",
                "meeting_id": 1,
                "stable": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projection/1",
            {
                "meeting_id": 1,
                "stable": True,
                "current_projector_id": 23,
                "content_object_id": "poll/788",
            },
        )
        projector = self.get_model("projector/23")
        assert projector.get("current_projection_ids") == [1]

    def test_toggle_unstable_move_into_history(self) -> None:
        self.setup_models(False)
        self.set_models(
            {
                "poll/888": {"meeting_id": 1},
                "projector/23": {"scroll": 100},
            }
        )
        response = self.request(
            "projector.toggle",
            {
                "ids": [23],
                "content_object_id": "poll/888",
                "meeting_id": 1,
                "stable": False,
            },
        )
        self.assert_status_code(response, 200)
        projector = self.get_model("projector/23")
        assert projector.get("current_projection_ids") == [34]
        assert projector.get("history_projection_ids") == [33]
        assert projector.get("scroll") == 0
        self.assert_model_exists("projection/34")

    def test_toggle_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "projector.toggle",
            {"ids": [23], "content_object_id": "poll/788", "meeting_id": 1},
        )

    def test_toggle_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "projector.toggle",
            {"ids": [23], "content_object_id": "poll/788", "meeting_id": 1},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_toggle_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "projector.toggle",
            {"ids": [23], "content_object_id": "poll/788", "meeting_id": 1},
        )
