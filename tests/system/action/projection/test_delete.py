from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectionDelete(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {"all_projection_ids": [12, 13], "projector_ids": [1]},
                "projector/1": {
                    "current_projection_ids": [12],
                    "meeting_id": 1,
                    "preview_projection_ids": [13],
                    "history_projection_ids": [14],
                },
                "projection/12": {"current_projector_id": 1, "meeting_id": 1},
                "projection/13": {"preview_projector_id": 1, "meeting_id": 1},
                "projection/14": {"history_projector_id": 1, "meeting_id": 1},
            }
        )

    def test_delete_current_correct(self) -> None:
        response = self.request("projection.delete", {"id": 12})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("projection/12")

    def test_delete_preview_correct(self) -> None:
        response = self.request("projection.delete", {"id": 13})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("projection/13")

    def test_delete_history_not_allowed(self) -> None:
        response = self.request("projection.delete", {"id": 14})
        self.assert_status_code(response, 400)
        assert (
            "Projection must have a current_projector_id or a preview_projector_id."
            in response.json["message"]
        )
        self.assert_model_exists("projection/13")

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test({}, "projection.delete", {"id": 12})

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projection.delete",
            {"id": 12},
            Permissions.Projector.CAN_MANAGE,
        )
