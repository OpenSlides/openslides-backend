from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorSortPreview(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "projection/1": {
                    "meeting_id": 1,
                    "preview_projector_id": 1,
                    "weight": 10,
                    "content_object_id": "meeting/1",
                },
                "projection/2": {
                    "meeting_id": 1,
                    "preview_projector_id": 1,
                    "weight": 11,
                    "content_object_id": "meeting/1",
                },
                "projection/3": {
                    "meeting_id": 1,
                    "preview_projector_id": 1,
                    "weight": 12,
                    "content_object_id": "meeting/1",
                },
            }
        )

    def test_sort_preview(self) -> None:
        response = self.request(
            "projector.sort_preview", {"id": 1, "projection_ids": [2, 3, 1]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("projection/2", {"weight": 1})
        self.assert_model_exists("projection/3", {"weight": 2})
        self.assert_model_exists("projection/1", {"weight": 3})

    def test_sort_preview_not_correct_ids(self) -> None:
        response = self.request(
            "projector.sort_preview", {"id": 1, "projection_ids": [2, 3]}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Must give all preview projections of this projector and nothing else.",
            response.json["message"],
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
