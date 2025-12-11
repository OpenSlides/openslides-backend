from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectionUpdateOptions(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "projection/33": {
                    "meeting_id": 1,
                    "current_projector_id": 1,
                    "content_object_id": "meeting/1",
                },
            }
        )

    def test_correct(self) -> None:
        response = self.request(
            "projection.update_options", {"id": 33, "options": {"bla": []}}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("projection/33", {"options": {"bla": []}})

    def test_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projection.update_options",
            {"id": 33, "options": {"bla": []}},
        )

    def test_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projection.update_options",
            {"id": 33, "options": {"bla": []}},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projection.update_options",
            {"id": 33, "options": {"bla": []}},
        )
