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
        projector_message = self.get_model("projector_message/1")
        assert projector_message.get("meeting_id") == 1
        assert projector_message.get("message") == "&lt;b&gt;TEST&lt;/b&gt;"
        meeting = self.get_model("meeting/1")
        assert meeting.get("projector_message_ids") == [1]

    def test_create_empty_data(self) -> None:
        response = self.request("projector_message.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'message'] properties",
            response.json["message"],
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector_message.create",
            {
                "meeting_id": 1,
                "message": "<b>TEST</b>",
            },
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector_message.create",
            {
                "meeting_id": 1,
                "message": "<b>TEST</b>",
            },
            Permissions.Projector.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector_message.create",
            {
                "meeting_id": 1,
                "message": "<b>TEST</b>",
            },
        )
