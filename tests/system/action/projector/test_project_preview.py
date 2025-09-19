from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorProjectPreview(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "projector/2": {"meeting_id": 1, "sequential_number": 2},
                "projection/1": {
                    "current_projector_id": 1,
                    "meeting_id": 1,
                    "weight": 100,
                    "stable": True,
                    "content_object_id": "meeting/1",
                },
                "projection/2": {
                    "current_projector_id": 1,
                    "meeting_id": 1,
                    "weight": 98,
                    "content_object_id": "meeting/1",
                },
                "projection/3": {
                    "preview_projector_id": 1,
                    "meeting_id": 1,
                    "weight": 99,
                    "content_object_id": "meeting/1",
                },
                "projection/4": {
                    "preview_projector_id": 1,
                    "meeting_id": 1,
                    "weight": 100,
                    "content_object_id": "meeting/1",
                },
                "projection/5": {
                    "history_projector_id": 1,
                    "meeting_id": 1,
                    "weight": 50,
                    "content_object_id": "meeting/1",
                },
                "projection/6": {
                    "preview_projector_id": 2,
                    "meeting_id": 1,
                    "weight": 100,
                    "content_object_id": "meeting/1",
                },
            }
        )

    def test_project_preview_nothing(self) -> None:
        response = self.request("projector.project_preview", {"id": 2})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Projection has not a preview_projector_id.", response.json["message"]
        )
        self.assert_model_exists(
            "projector/1",
            {
                "current_projection_ids": [1, 2],
                "preview_projection_ids": [3, 4],
                "history_projection_ids": [5],
            },
        )

    def test_project_preview_complex(self) -> None:
        response = self.request("projector.project_preview", {"id": 3})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/1",
            {
                "current_projection_ids": [1, 3],
                "preview_projection_ids": [4],
                "history_projection_ids": [2, 5],
            },
        )

        self.assert_model_exists("projection/1", {"weight": 100})
        self.assert_model_exists("projection/2", {"weight": 51})

    def test_project_preview_just_preview(self) -> None:
        response = self.request("projector.project_preview", {"id": 6})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/2",
            {
                "current_projection_ids": [6],
                "preview_projection_ids": None,
                "history_projection_ids": None,
            },
        )

    def test_project_preview_no_permissions(self) -> None:
        self.base_permission_test({}, "projector.project_preview", {"id": 3})

    def test_project_preview_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.project_preview",
            {"id": 3},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_project_preview_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector.project_preview",
            {"id": 3},
        )
