from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class StructureLevelCreateTest(BaseActionTestCase):
    def test_create_empty_data(self) -> None:
        response = self.request("structure_level.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'name'] properties",
            response.json["message"],
        )

    def test_create_required_fields(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request(
            "structure_level.create",
            {
                "name": "test",
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level/1",
            {
                "name": "test",
                "meeting_id": 1,
            },
        )
        self.assert_model_exists(
            "meeting/1",
            {
                "structure_level_ids": [1],
            },
        )

    def test_create_all_fields(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request(
            "structure_level.create",
            {
                "name": "test",
                "meeting_id": 1,
                "color": "#abf257",
                "default_time": 600,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level/1",
            {
                "name": "test",
                "meeting_id": 1,
                "color": "#abf257",
                "default_time": 600,
            },
        )

    def test_create_duplicate_name(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "is_active_in_organization_id": 1,
                    "structure_level_ids": [1],
                },
                "structure_level/1": {"meeting_id": 1, "name": "test"},
            }
        )
        response = self.request(
            "structure_level.create",
            {
                "name": "test",
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The name of the structure level must be unique.",
            response.json["message"],
        )
        self.assert_model_not_exists("structure_level/2")

    def test_create_duplicate_name_in_other_meeting(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "meeting/2": {
                    "is_active_in_organization_id": 1,
                    "structure_level_ids": [1],
                },
                "structure_level/1": {"meeting_id": 2, "name": "test"},
            }
        )
        response = self.request(
            "structure_level.create",
            {
                "name": "test",
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level/2",
            {
                "name": "test",
                "meeting_id": 1,
            },
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "structure_level.create",
            {
                "name": "test",
                "meeting_id": 1,
            },
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {},
            "structure_level.create",
            {
                "name": "test",
                "meeting_id": 1,
            },
            Permissions.User.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "structure_level.create",
            {
                "name": "test",
                "meeting_id": 1,
            },
        )
