from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class UserMergeTogether(BaseActionTestCase):
    def test_not_implemented_with_superadmin(self) -> None:
        response = self.request(
            "user.merge_together", {"username": "new user", "user_ids": []}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "This action is still not implemented, but permission checked",
            response.json["message"],
        )

    def test_empty_payload_fields(self) -> None:
        response = self.request("user.merge_together", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['user_ids', 'username'] properties",
            response.json["message"],
        )

    def test_correct_permission(self) -> None:
        self.user_id = self.create_user(
            "test",
            organization_management_level=OrganizationManagementLevel.CAN_MANAGE_USERS,
        )
        self.login(self.user_id)
        response = self.request(
            "user.merge_together", {"username": "new user", "user_ids": []}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "This action is still not implemented, but permission checked",
            response.json["message"],
        )

    def test_missing_permission(self) -> None:
        self.user_id = self.create_user("test")
        self.login(self.user_id)
        response = self.request(
            "user.merge_together", {"username": "new user", "user_ids": []}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.merge_together. Missing OrganizationManagementLevel: can_manage_users",
            response.json["message"],
        )
