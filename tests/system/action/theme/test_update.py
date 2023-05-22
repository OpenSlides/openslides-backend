from tests.system.action.base import BaseActionTestCase


class ThemeUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models({"theme/1": {"name": "old"}})
        response = self.request(
            "theme.update", {"id": 1, "name": "test", "primary_500": "#121212"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("theme/1", {"name": "test", "primary_500": "#121212"})

    def test_update_opt_fields_correct(self) -> None:
        self.set_models({"theme/1": {"name": "old"}})
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
        self.set_models(
            {
                "user/1": {"organization_management_level": "can_manage_users"},
                "theme/1": {"name": "test", "primary_500": "#000000"},
            }
        )
        response = self.request(
            "theme.update", {"id": 1, "name": "test", "primary_500": "#121212"}
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action theme.update. Missing OrganizationManagementLevel: can_manage_organization"
            in response.json["message"]
        )

    def test_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": "can_manage_organization"},
                "theme/1": {"name": "old", "primary_500": "#000000"},
            }
        )
        response = self.request(
            "theme.update", {"id": 1, "name": "test", "primary_500": "#121212"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("theme/1", {"name": "test", "primary_500": "#121212"})
