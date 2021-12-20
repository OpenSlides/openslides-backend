from openslides_backend.permissions.management_levels import OrganizationManagementLevel

from .base import BasePresenterTestCase


class TestGetActiveUsersAmount(BasePresenterTestCase):
    def test_correct(self) -> None:
        self.set_models(
            {
                "user/2": {"is_active": True},
                "user/3": {"is_active": False},
                "user/4": {"is_active": True},
                "user/5": {"is_active": False},
            }
        )
        status_code, data = self.request("get_active_users_amount", {})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"active_users_amount": 3})

    def test_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                }
            }
        )
        status_code, data = self.request("get_active_users_amount", {})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"active_users_amount": 1})

    def test_no_permissions(self) -> None:
        self.set_models({"user/1": {"organization_management_level": None}})
        status_code, data = self.request("get_active_users_amount", {})
        self.assertEqual(status_code, 403)
