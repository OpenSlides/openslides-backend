from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class ThemeUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        response = self.request(
            "theme.update", {"id": 1, "name": "test", "primary_500": "#121212"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("theme/1", {"name": "test", "primary_500": "#121212"})

    def test_update_opt_fields_correct(self) -> None:
        response = self.request(
            "theme.update",
            {
                "id": 1,
                "name": "test",
                "headbar": "#333444",
                "yes": "#333555",
                "no": "#333666",
                "abstain": "#333777",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "theme/1",
            {
                "name": "test",
                "headbar": "#333444",
                "yes": "#333555",
                "no": "#333666",
                "abstain": "#333777",
            },
        )

    def test_no_permission(self) -> None:
        self.base_permission_test(
            {},
            "theme.update",
            {"id": 1, "name": "test"},
            OrganizationManagementLevel.CAN_MANAGE_USERS,
            fail=True,
        )

    def test_permission(self) -> None:
        self.base_permission_test(
            {},
            "theme.update",
            {"id": 1, "name": "test"},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
