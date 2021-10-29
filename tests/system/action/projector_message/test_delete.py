from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorMessageDelete(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/2": {
                    "projector_message_ids": [2],
                    "is_active_in_organization_id": 1,
                },
                "projector_message/2": {"meeting_id": 2, "message": "test1"},
            }
        )
        self.permission_test_model = {
            "projector_message/2": {"meeting_id": 1, "message": "test1"},
        }

    def test_delete_correct(self) -> None:
        response = self.request("projector_message.delete", {"id": 2})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("projector_message/2")

    def test_delete_wrong_id(self) -> None:
        response = self.request("projector_message.delete", {"id": 3})
        self.assert_status_code(response, 400)
        model = self.get_model("projector_message/2")
        assert model.get("message") == "test1"

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "projector_message.delete",
            {"id": 2},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "projector_message.delete",
            {"id": 2},
            Permissions.Projector.CAN_MANAGE,
        )
