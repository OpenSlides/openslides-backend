from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class GroupSetPermissionActionTest(BaseActionTestCase):
    def test_set_permission_set_true(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/11": {
                    "name": "group_11",
                    "permissions": ["agenda_item.can_manage", "motion.can_create"],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "group.set_permission",
            {"id": 11, "permission": "projector.can_see", "set": True},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/11")
        assert model.get("permissions") == [
            "agenda_item.can_manage",
            "motion.can_create",
            "projector.can_see",
        ]

    def test_set_permission_reset(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/11": {
                    "name": "group_11",
                    "permissions": ["agenda_item.can_manage", "motion.can_create"],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "group.set_permission",
            {"id": 11, "permission": "agenda_item.can_manage", "set": True},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/11")
        assert model.get("permissions") == [
            "agenda_item.can_manage",
            "motion.can_create",
        ]

    def test_set_permission_set_false(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/11": {
                    "name": "group_11",
                    "permissions": ["agenda_item.can_manage", "motion.can_create"],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "group.set_permission",
            {"id": 11, "permission": "agenda_item.can_manage", "set": False},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/11")
        assert model.get("permissions") == ["motion.can_create"]

    def test_set_permission_reunset(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/11": {
                    "name": "group_11",
                    "permissions": ["agenda_item.can_manage"],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "group.set_permission",
            {"id": 11, "permission": "motion.can_create", "set": False},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/11")
        assert model.get("permissions") == ["agenda_item.can_manage"]

    def test_set_permissions_missing_permissions_in_group(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/11": {
                    "name": "group_11",
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "group.set_permission",
            {"id": 11, "permission": "motion.can_create", "set": True},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/11")
        assert model.get("permissions") == ["motion.can_create"]

    def test_set_permissions_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "group/11": {
                    "name": "group_11",
                    "permissions": ["agenda_item.can_manage", "motion.can_create"],
                    "meeting_id": 1,
                },
            },
            "group.set_permission",
            {"id": 11, "permission": "projector.can_see", "set": True},
        )

    def test_set_permissions_permissions(self) -> None:
        self.base_permission_test(
            {
                "group/11": {
                    "name": "group_11",
                    "permissions": ["agenda_item.can_manage", "motion.can_create"],
                    "meeting_id": 1,
                },
            },
            "group.set_permission",
            {"id": 11, "permission": "projector.can_see", "set": True},
            Permissions.User.CAN_MANAGE,
        )
