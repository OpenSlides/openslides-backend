from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class ThemeCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        response = self.request(
            "theme.create",
            {
                "name": "test_Xcdfgee",
                "primary_500": "#111222",
                "accent_500": "#111222",
                "warn_500": "#222333",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "theme/2",
            {
                "name": "test_Xcdfgee",
                "primary_500": "#111222",
                "accent_500": "#111222",
                "warn_500": "#222333",
                "organization_id": 1,
            },
        )

    def test_create_opt_fields(self) -> None:
        response = self.request(
            "theme.create",
            {
                "name": "test_Xcdfgee",
                "primary_500": "#111222",
                "accent_500": "#111222",
                "warn_500": "#222333",
                "headbar": "#333444",
                "yes": "#333555",
                "no": "#333666",
                "abstain": "#333777",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "theme/2",
            {
                "name": "test_Xcdfgee",
                "primary_500": "#111222",
                "accent_500": "#111222",
                "warn_500": "#222333",
                "headbar": "#333444",
                "yes": "#333555",
                "no": "#333666",
                "abstain": "#333777",
                "organization_id": 1,
            },
        )

    def test_create_empty_data(self) -> None:
        response = self.request("theme.create", {})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action theme.create: data must contain ['accent_500', 'name', 'primary_500', 'warn_500'] properties",
            response.json["message"],
        )

    def test_create_permission(self) -> None:
        self.base_permission_test(
            {},
            "theme.create",
            {
                "name": "test_Xcdfgee",
                "primary_500": "#111222",
                "accent_500": "#111222",
                "warn_500": "#222333",
            },
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )

    def test_create_no_permission(self) -> None:
        self.base_permission_test(
            {},
            "theme.create",
            {
                "name": "test_Xcdfgee",
                "primary_500": "#111222",
                "accent_500": "#111222",
                "warn_500": "#222333",
            },
        )
