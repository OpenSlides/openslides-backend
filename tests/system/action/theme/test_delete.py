from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class ThemeDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "theme_id": 2,
                    "theme_ids": [1, 2],
                },
                "theme/1": {
                    "name": "test",
                    "primary_500": "#000000",
                    "organization_id": 1,
                    "theme_for_organization_id": None,
                },
                "theme/2": {
                    "name": "OpenSlides Test",
                    "organization_id": 1,
                    "theme_for_organization_id": 1,
                },
            },
        )
        response = self.request("theme.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("theme/1")

    def test_delete_fail_to_delete_theme_from_orga(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"theme_ids": [1], "theme_id": 1},
                "theme/1": {
                    "name": "test",
                    "organization_id": 1,
                    "theme_for_organization_id": 1,
                },
            }
        )
        response = self.request("theme.delete", {"id": 1})
        self.assert_status_code(response, 400)
        assert (
            "Update of organization/1: You try to set following required fields to an empty value: ['theme_id']"
            in response.json["message"]
        )

    def test_no_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": "can_manage_users"},
                "theme/1": {"name": "test", "primary_500": "#000000"},
            }
        )
        response = self.request("theme.delete", {"id": 1})
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action theme.delete. Missing OrganizationManagementLevel: can_manage_organization"
            in response.json["message"]
        )

    def test_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": "can_manage_organization"},
                "theme/1": {"name": "test", "primary_500": "#000000"},
            }
        )
        response = self.request("theme.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("theme/1")
