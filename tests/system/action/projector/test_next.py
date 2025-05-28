from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorNext(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "projector/2": {"meeting_id": 1},
                "projector/3": {
                    "current_projection_ids": [1, 2],
                    "preview_projection_ids": [3, 4],
                    "history_projection_ids": [6],
                    "meeting_id": 1,
                },
                "projector/4": {
                    "current_projection_ids": [],
                    "preview_projection_ids": [5],
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
                    "preview_projector_id": 4,
                    "meeting_id": 1,
                    "weight": 100,
                },
                "projection/6": {
                    "history_projector_id": 3,
                    "meeting_id": 1,
                    "weight": 50,
                },
            }
        )

    def test_next_nothing(self) -> None:
        response = self.request("projector.next", {"id": 2})
        self.assert_status_code(response, 200)
        projector = self.get_model("projector/2")
        assert projector.get("current_projection_ids") is None
        assert projector.get("preview_projection_ids") is None
        assert projector.get("history_projection_ids") is None

    def test_next_complex(self) -> None:
        response = self.request("projector.next", {"id": 3})
        self.assert_status_code(response, 200)
        projector = self.get_model("projector/3")
        assert projector.get("current_projection_ids") == [1, 3]
        assert projector.get("preview_projection_ids") == [4]
        assert projector.get("history_projection_ids") == [6, 2]
        projection_1 = self.get_model("projection/1")
        assert projection_1.get("weight") == 100
        projection_2 = self.get_model("projection/2")
        assert projection_2.get("weight") == 51

    def test_next_just_preview(self) -> None:
        response = self.request("projector.next", {"id": 4})
        self.assert_status_code(response, 200)
        projector = self.get_model("projector/4")
        assert projector.get("current_projection_ids") == [5]
        assert projector.get("preview_projection_ids") == []
        assert projector.get("history_projection_ids") == []

    def test_next_no_permissions(self) -> None:
        self.base_permission_test({}, "projector.next", {"id": 4})

    def test_next_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.next",
            {"id": 4},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_next_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector.next",
            {"id": 4},
        )
