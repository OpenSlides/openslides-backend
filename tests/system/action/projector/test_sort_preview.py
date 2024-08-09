from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorSortPreview(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "projector/1": {"meeting_id": 1, "preview_projection_ids": [1, 2, 3]},
                "projection/1": {
                    "meeting_id": 1,
                    "preview_projector_id": 1,
                    "weight": 10,
                },
                "projection/2": {
                    "meeting_id": 1,
                    "preview_projector_id": 1,
                    "weight": 11,
                },
                "projection/3": {
                    "meeting_id": 1,
                    "preview_projector_id": 1,
                    "weight": 12,
                },
            }
        )

    def test_sort_preview(self) -> None:
        response = self.request(
            "projector.sort_preview", {"id": 1, "projection_ids": [2, 3, 1]}
        )
        self.assert_status_code(response, 200)
        projection_2 = self.get_model("projection/2")
        assert projection_2.get("weight") == 1
        projection_3 = self.get_model("projection/3")
        assert projection_3.get("weight") == 2
        projection_1 = self.get_model("projection/1")
        assert projection_1.get("weight") == 3

    def test_sort_preview_not_correct_ids(self) -> None:
        response = self.request(
            "projector.sort_preview", {"id": 1, "projection_ids": [2, 3]}
        )
        self.assert_status_code(response, 400)
        assert (
            "Must give all preview projections of this projector and nothing else."
            in response.json["message"]
        )

    def test_sort_no_permissions(self) -> None:
        self.base_permission_test(
            {}, "projector.sort_preview", {"id": 1, "projection_ids": [2, 3, 1]}
        )

    def test_sort_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.sort_preview",
            {"id": 1, "projection_ids": [2, 3, 1]},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_sort_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector.sort_preview",
            {"id": 1, "projection_ids": [2, 3, 1]},
        )
