from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorMessageUpdate(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models({"projector_message/2": {"meeting_id": 1, "message": "test1"}})

    def test_update(self) -> None:
        response = self.request(
            "projector_message.update",
            {"id": 2, "message": "geredegerede"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("projector_message/2", {"message": "geredegerede"})

    def test_update_wrong_id(self) -> None:
        response = self.request(
            "projector_message.update",
            {"id": 3, "message": "geredegerede"},
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("projector_message/2", {"message": "test1"})

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector_message.update",
            {"id": 2, "message": "geredegerede"},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector_message.update",
            {"id": 2, "message": "geredegerede"},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector_message.update",
            {"id": 2, "message": "geredegerede"},
        )
