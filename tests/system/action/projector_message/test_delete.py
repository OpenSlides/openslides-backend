from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorMessageDelete(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "projector_message/2": {"meeting_id": 1, "message": "test1"},
                "projection/1": {
                    "content_object_id": "projector_message/2",
                    "current_projector_id": 1,
                    "meeting_id": 1,
                },
            }
        )

    def test_delete_correct(self) -> None:
        response = self.request("projector_message.delete", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("projector_message/2")
        self.assert_model_not_exists("projection/1")

    def test_delete_wrong_id(self) -> None:
        response = self.request("projector_message.delete", {"id": 3})
        self.assert_status_code(response, 400)
        self.assert_model_exists("projector_message/2", {"message": "test1"})

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector_message.delete",
            {"id": 2},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector_message.delete",
            {"id": 2},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector_message.delete",
            {"id": 2},
        )
