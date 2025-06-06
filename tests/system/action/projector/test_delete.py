from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorDelete(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "projector/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 1,
                    "used_as_default_projector_for_motion_in_meeting_id": 1,
                },
                "projector/113": {
                    "name": "name_test1",
                    "used_as_reference_projector_meeting_id": 1,
                    "meeting_id": 1,
                },
                "meeting/1": {
                    "reference_projector_id": 113,
                    "default_projector_motion_ids": [111],
                    "projector_ids": [111, 113],
                },
            }
        )

    def test_delete_correct(self) -> None:
        response = self.request("projector.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("projector/111")
        meeting = self.get_model("meeting/1")
        assert meeting.get("default_projector_motion_ids") == [113]
        self.assert_model_exists(
            "projector/113",
            {
                "used_as_default_projector_for_motion_in_meeting_id": 1,
                "used_as_reference_projector_meeting_id": 1,
            },
        )

    def test_delete_with_projections(self) -> None:
        self.set_models(
            {
                "projector/111": {
                    "preview_projection_ids": [1],
                    "current_projection_ids": [2],
                    "history_projection_ids": [3],
                },
                "projection/1": {
                    "preview_projector_id": 111,
                    "content_object_id": "meeting/1",
                    "meeting_id": 1,
                },
                "projection/2": {
                    "current_projector_id": 111,
                    "content_object_id": "meeting/1",
                    "meeting_id": 1,
                },
                "projection/3": {
                    "history_projector_id": 111,
                    "content_object_id": "meeting/1",
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("projector.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("projector/111")
        self.assert_model_not_exists("projection/1")
        self.assert_model_not_exists("projection/2")
        self.assert_model_not_exists("projection/3")

    def test_delete_prevent_if_used_as_reference(self) -> None:
        response = self.request("projector.delete", {"id": 113})
        self.assert_status_code(response, 400)
        assert (
            "A used as reference projector is not allowed to delete."
            in response.data.decode()
        )
        model = self.get_model("projector/113")
        assert model.get("name") == "name_test1"

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test({}, "projector.delete", {"id": 111})

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.delete",
            {"id": 111},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector.delete",
            {"id": 111},
        )
