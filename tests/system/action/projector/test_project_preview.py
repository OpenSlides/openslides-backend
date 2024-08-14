from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorProjectPreview(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "projector/2": {"meeting_id": 1},
                "projector/3": {
                    "current_projection_ids": [1, 2],
                    "preview_projection_ids": [3, 4],
                    "history_projection_ids": [5],
                    "meeting_id": 1,
                },
                "projector/4": {
                    "current_projection_ids": [],
                    "preview_projection_ids": [6],
                    "history_projection_ids": [],
                    "meeting_id": 1,
                },
                "projection/1": {
                    "current_projector_id": 3,
                    "meeting_id": 1,
                    "weight": 100,
                    "stable": True,
                },
                "projection/2": {
                    "current_projector_id": 3,
                    "meeting_id": 1,
                    "weight": 98,
                },
                "projection/3": {
                    "preview_projector_id": 3,
                    "meeting_id": 1,
                    "weight": 99,
                },
                "projection/4": {
                    "preview_projector_id": 3,
                    "meeting_id": 1,
                    "weight": 100,
                },
                "projection/5": {
                    "history_projector_id": 3,
                    "meeting_id": 1,
                    "weight": 50,
                },
                "projection/6": {
                    "preview_projector_id": 4,
                    "meeting_id": 1,
                    "weight": 100,
                },
            }
        )

    def test_project_preview_nothing(self) -> None:
        response = self.request("projector.project_preview", {"id": 2})
        self.assert_status_code(response, 400)
        assert "Projection has not a preview_projector_id." in response.json["message"]
        projector = self.get_model("projector/3")
        assert projector.get("current_projection_ids") == [1, 2]
        assert projector.get("preview_projection_ids") == [3, 4]
        assert projector.get("history_projection_ids") == [5]

    def test_project_preview_complex(self) -> None:
        response = self.request("projector.project_preview", {"id": 3})
        self.assert_status_code(response, 200)
        projector = self.get_model("projector/3")
        assert projector.get("current_projection_ids") == [1, 3]
        assert projector.get("preview_projection_ids") == [4]
        assert projector.get("history_projection_ids") == [5, 2]
        projection_1 = self.get_model("projection/1")
        assert projection_1.get("weight") == 100
        projection_2 = self.get_model("projection/2")
        assert projection_2.get("weight") == 51

    def test_project_preview_just_preview(self) -> None:
        response = self.request("projector.project_preview", {"id": 6})
        self.assert_status_code(response, 200)
        projector = self.get_model("projector/4")
        assert projector.get("current_projection_ids") == [6]
        assert projector.get("preview_projection_ids") == []
        assert projector.get("history_projection_ids") == []

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
