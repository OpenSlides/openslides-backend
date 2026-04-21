from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions

from .base import BasePresenterTestCase


class TestGetValidTimezones(BasePresenterTestCase):
    def test_get_as_accountadmin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        status_code, data = self.request("get_valid_timezones", {})
        self.assertEqual(status_code, 403)
        assert data["message"] == "Missing Permission: meeting.can_manage_settings"

    def test_get_with_no_meeting_perms(self) -> None:
        self.create_meeting(1)
        self.set_user_groups(1, [1])
        self.set_organization_management_level(None)
        status_code, data = self.request("get_valid_timezones", {})
        self.assertEqual(status_code, 403)
        assert data["message"] == "Missing Permission: meeting.can_manage_settings"

    def test_get_with_no_perms(self) -> None:
        self.set_organization_management_level(None)
        status_code, data = self.request("get_valid_timezones", {})
        self.assertEqual(status_code, 403)
        assert data["message"] == "Missing Permission: meeting.can_manage_settings"

    def test_get(self) -> None:
        status_code, data = self.request("get_valid_timezones", {})
        self.assertEqual(status_code, 200)
        assert isinstance(data, dict)
        # Checking for Korea bc no DST, therfore just one possible abbreviation.
        assert data.get("Asia/Seoul") == "KST"

    def test_get_as_orgaadmin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        status_code, data = self.request("get_valid_timezones", {})
        self.assertEqual(status_code, 200)
        assert isinstance(data, dict)
        assert data.get("Asia/Seoul") == "KST"

    def test_get_as_committee_admin(self) -> None:
        self.create_meeting(1)
        self.set_committee_management_level([60])
        self.set_organization_management_level(None)
        status_code, data = self.request("get_valid_timezones", {})
        self.assertEqual(status_code, 200)
        assert isinstance(data, dict)
        assert data.get("Asia/Seoul") == "KST"

    def test_get_as_meeting_admin(self) -> None:
        self.create_meeting(1)
        self.set_user_groups(1, [2])
        self.set_organization_management_level(None)
        status_code, data = self.request("get_valid_timezones", {})
        self.assertEqual(status_code, 200)
        assert isinstance(data, dict)
        assert data.get("Asia/Seoul") == "KST"

    def test_get_with_meeting_can_manage_settings(self) -> None:
        self.create_meeting(1)
        self.set_user_groups(1, [1])
        self.set_group_permissions(1, [Permissions.Meeting.CAN_MANAGE_SETTINGS])
        self.set_organization_management_level(None)
        status_code, data = self.request("get_valid_timezones", {})
        self.assertEqual(status_code, 200)
        assert isinstance(data, dict)
        assert data.get("Asia/Seoul") == "KST"
