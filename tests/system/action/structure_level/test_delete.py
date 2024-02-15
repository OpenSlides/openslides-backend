from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class StructureLevelDeleteTest(BaseActionTestCase):
    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "structure_level/1": {"meeting_id": 1, "name": "test"},
            },
            "structure_level.delete",
            {
                "id": 1,
            },
        )
        self.assert_model_exists("structure_level/1")

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            {
                "structure_level/1": {"meeting_id": 1, "name": "test"},
            },
            "structure_level.delete",
            {
                "id": 1,
            },
            Permissions.User.CAN_MANAGE,
        )
        self.assert_model_deleted("structure_level/1")
