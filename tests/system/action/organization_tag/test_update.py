from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class OrganizationTagUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models({"organization_tag/1": {"name": "old", "color": "#000000"}})

    def test_update_correct(self) -> None:
        response = self.request(
            "organization_tag.update", {"id": 1, "name": "test", "color": "#121212"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "organization_tag/1", {"name": "test", "color": "#121212"}
        )

    def test_no_permission(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request(
            "organization_tag.update", {"id": 1, "name": "test", "color": "#121212"}
        )
        self.assert_status_code(response, 403)
        self.assertEqual(
            "You are not allowed to perform action organization_tag.update. Missing OrganizationManagementLevel: can_manage_organization",
            response.json["message"],
        )

    def test_permission(self) -> None:
        self.base_permission_test(
            {},
            "organization_tag.update",
            {"id": 1, "name": "test", "color": "#121212"},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
        self.assert_model_exists(
            "organization_tag/1", {"name": "test", "color": "#121212"}
        )
