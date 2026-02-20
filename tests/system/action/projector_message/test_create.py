from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorMessageCreate(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_create(self) -> None:
        response = self.request(
            "projector_message.create",
            {
                "meeting_id": 1,
                "message": "<b>TEST</b>",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector_message/1",
            {"meeting_id": 1, "message": "&lt;b&gt;TEST&lt;/b&gt;"},
        )
        self.assert_model_exists("meeting/1", {"projector_message_ids": [1]})

    def test_create_empty_data(self) -> None:
        response = self.request("projector_message.create", {})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action projector_message.create: data must contain ['meeting_id', 'message'] properties",
            response.json["message"],
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector_message.create",
            {"meeting_id": 1, "message": "<b>TEST</b>"},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector_message.create",
            {"meeting_id": 1, "message": "<b>TEST</b>"},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector_message.create",
            {"meeting_id": 1, "message": "<b>TEST</b>"},
        )
