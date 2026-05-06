from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class ThemeDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.theme_2 = {"theme/2": {"name": "OpenSlides Test", "organization_id": 1}}

    def test_delete_correct(self) -> None:
        self.set_models(self.theme_2)
        response = self.request("theme.delete", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("theme/2")

    def test_delete_fail_to_delete_theme_from_orga(self) -> None:
        response = self.request("theme.delete", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Update of organization/1: You try to set following required fields to an empty value: ['theme_id']",
            response.json["message"],
        )

    def test_no_permission(self) -> None:
        self.base_permission_test(
            self.theme_2,
            "theme.delete",
            {"id": 2},
            OrganizationManagementLevel.CAN_MANAGE_USERS,
            fail=True,
        )

    def test_permission(self) -> None:
        self.base_permission_test(
            self.theme_2,
            "theme.delete",
            {"id": 2},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
