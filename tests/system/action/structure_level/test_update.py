from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class StructureLevelUpdateTest(BaseActionTestCase):
    def test_update_all_fields(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {
                    "structure_level_ids": [1],
                },
                "structure_level/1": {"meeting_id": 1, "name": "test"},
            }
        )
        response = self.request(
            "structure_level.update",
            {
                "id": 1,
                "name": "test2",
                "color": "#abf257",
                "default_time": 600,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level/1",
            {
                "name": "test2",
                "meeting_id": 1,
                "color": "#abf257",
                "default_time": 600,
            },
        )

    def test_update_duplicate_name(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {
                    "structure_level_ids": [1, 2],
                },
                "structure_level/1": {"meeting_id": 1, "name": "test"},
                "structure_level/2": {"meeting_id": 1, "name": "test2"},
            }
        )
        response = self.request(
            "structure_level.update",
            {
                "id": 1,
                "name": "test2",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The name of the structure level must be unique.",
            response.json["message"],
        )
        self.assert_model_exists("structure_level/1", {"name": "test"})

    def test_update_duplicate_name_in_other_meeting(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {
                    "structure_level_ids": [1],
                },
                "meeting/2": {
                    "is_active_in_organization_id": 1,
                    "structure_level_ids": [2],
                    "committee_id": 1,
                },
                "structure_level/1": {"meeting_id": 1, "name": "test"},
                "structure_level/2": {"meeting_id": 2, "name": "test2"},
            }
        )
        response = self.request(
            "structure_level.update",
            {
                "id": 1,
                "name": "test2",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level/1",
            {
                "name": "test2",
                "meeting_id": 1,
            },
        )

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "structure_level/1": {"meeting_id": 1, "name": "test"},
            },
            "structure_level.update",
            {
                "id": 1,
                "name": "test2",
            },
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {
                "structure_level/1": {"meeting_id": 1, "name": "test"},
            },
            "structure_level.update",
            {
                "id": 1,
                "name": "test2",
            },
            Permissions.User.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "structure_level/1": {"meeting_id": 1, "name": "test"},
            },
            "structure_level.update",
            {
                "id": 1,
                "name": "test2",
            },
        )
