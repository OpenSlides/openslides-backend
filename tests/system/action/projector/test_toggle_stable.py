from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorToggleStable(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model = {
            "projector/23": {"meeting_id": 1, "current_projection_ids": []},
            "poll/788": {"meeting_id": 1},
        }

    def test_correct_remove_projection(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "projector/23": {"meeting_id": 1, "current_projection_ids": [33]},
                "projection/33": {
                    "meeting_id": 1,
                    "content_object_id": "poll/788",
                    "current_projector_id": 23,
                    "stable": True,
                },
                "poll/788": {"meeting_id": 1},
            }
        )
        response = self.request(
            "projector.toggle_stable", {"ids": [23], "content_object_id": "poll/788"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("projection/33")
        projector = self.get_model("projector/23")
        assert projector.get("current_projection_ids") == []

    def test_correct_add_projection(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "projector/23": {"meeting_id": 1, "current_projection_ids": []},
                "poll/788": {"meeting_id": 1},
            }
        )
        response = self.request(
            "projector.toggle_stable", {"ids": [23], "content_object_id": "poll/788"}
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

    def test_toggle_stable_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "projector.toggle_stable",
            {"ids": [23], "content_object_id": "poll/788"},
        )

    def test_toggle_stable_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "projector.toggle_stable",
            {"ids": [23], "content_object_id": "poll/788"},
            Permissions.Projector.CAN_MANAGE,
        )
