from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorPrevious(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "projector/2": {"meeting_id": 1},
                "projector/3": {
                    "current_projection_ids": [1, 2],
                    "preview_projection_ids": [3, 4],
                    "history_projection_ids": [5, 6],
                    "meeting_id": 1,
                },
                "projector/4": {
                    "current_projection_ids": [],
                    "preview_projection_ids": [],
                    "history_projection_ids": [7],
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
                    "weight": 60,
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
                    "weight": 60,
                },
                "projection/6": {
                    "history_projector_id": 3,
                    "meeting_id": 1,
                    "weight": 55,
                },
                "projection/7": {
                    "history_projector_id": 4,
                    "meeting_id": 1,
                    "weight": 100,
                },
            }
        )

    def test_previous_nothing(self) -> None:
        response = self.request("projector.previous", {"id": 2})
        self.assert_status_code(response, 200)
        projector = self.get_model("projector/2")
        assert projector.get("current_projection_ids") is None
        assert projector.get("preview_projection_ids") is None
        assert projector.get("history_projection_ids") is None

    def test_previous_complex(self) -> None:
        response = self.request("projector.previous", {"id": 3})
        self.assert_status_code(response, 200)
        projector = self.get_model("projector/3")
        assert projector.get("current_projection_ids") == [5, 1]
        assert projector.get("preview_projection_ids") == [2, 3, 4]
        assert projector.get("history_projection_ids") == [6]
        projection_2 = self.get_model("projection/2")
        assert projection_2.get("weight") == 98

    def test_previous_just_history(self) -> None:
        response = self.request("projector.previous", {"id": 4})
        self.assert_status_code(response, 200)
        projector = self.get_model("projector/4")
        assert projector.get("current_projection_ids") == [7]
        assert projector.get("preview_projection_ids") == []
        assert projector.get("history_projection_ids") == []

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
