from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorMessageDelete(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(2)
        self.set_models(
            {
                "meeting/2": {
                    "projector_message_ids": [2],
                    "all_projection_ids": [1],
                },
                "projector_message/2": {
                    "meeting_id": 2,
                    "message": "test1",
                    "projection_ids": [1],
                },
                "projection/1": {
                    "content_object_id": "projector_message/2",
                    "current_projector_id": 1,
                    "meeting_id": 2,
                },
                "projector/1": {
                    "current_projection_ids": [1],
                    "meeting_id": 2,
                },
            }
        )
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "projector_message/2": {"meeting_id": 1, "message": "test1"},
        }

    def test_delete_correct(self) -> None:
        response = self.request("projector_message.delete", {"id": 2})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("projector_message/2")
        self.assert_model_deleted("projection/1")

    def test_delete_wrong_id(self) -> None:
        response = self.request("projector_message.delete", {"id": 3})
        self.assert_status_code(response, 400)
        model = self.get_model("projector_message/2")
        assert model.get("message") == "test1"

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "projector_message.delete",
            {"id": 2},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "projector_message.delete",
            {"id": 2},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "projector_message.delete",
            {"id": 2},
        )
