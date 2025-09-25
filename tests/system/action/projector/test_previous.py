from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorPrevious(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "projector/2": {"meeting_id": 1, "sequential_number": 2},
                "projector/3": {"meeting_id": 1, "sequential_number": 3},
                "projector/4": {"meeting_id": 1, "sequential_number": 4},
                "projection/1": {
                    "current_projector_id": 3,
                    "meeting_id": 1,
                    "weight": 100,
                    "stable": True,
                    "content_object_id": "meeting/1",
                },
                "projection/2": {
                    "current_projector_id": 3,
                    "meeting_id": 1,
                    "weight": 60,
                    "content_object_id": "meeting/1",
                },
                "projection/3": {
                    "preview_projector_id": 3,
                    "meeting_id": 1,
                    "weight": 99,
                    "content_object_id": "meeting/1",
                },
                "projection/4": {
                    "preview_projector_id": 3,
                    "meeting_id": 1,
                    "weight": 100,
                    "content_object_id": "meeting/1",
                },
                "projection/5": {
                    "history_projector_id": 3,
                    "meeting_id": 1,
                    "weight": 60,
                    "content_object_id": "meeting/1",
                },
                "projection/6": {
                    "history_projector_id": 3,
                    "meeting_id": 1,
                    "weight": 55,
                    "content_object_id": "meeting/1",
                },
                "projection/7": {
                    "history_projector_id": 4,
                    "meeting_id": 1,
                    "weight": 100,
                    "content_object_id": "meeting/1",
                },
            }
        )

    def test_previous_nothing(self) -> None:
        response = self.request("projector.previous", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/2",
            {
                "current_projection_ids": None,
                "preview_projection_ids": None,
                "history_projection_ids": None,
            },
        )

    def test_previous_complex(self) -> None:
        response = self.request("projector.previous", {"id": 3})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/3",
            {
                "current_projection_ids": [1, 5],
                "preview_projection_ids": [2, 3, 4],
                "history_projection_ids": [6],
            },
        )
        self.assert_model_exists("projection/2", {"weight": 98})

    def test_previous_just_history(self) -> None:
        response = self.request("projector.previous", {"id": 4})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/4",
            {
                "current_projection_ids": [7],
                "preview_projection_ids": None,
                "history_projection_ids": None,
            },
        )

    def test_previous_no_permissions(self) -> None:
        self.base_permission_test({}, "projector.previous", {"id": 4})

    def test_previous_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.previous",
            {"id": 4},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_previous_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector.previous",
            {"id": 4},
        )
