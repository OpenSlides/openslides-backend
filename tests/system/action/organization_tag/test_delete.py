from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class OrganizationTagDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models({"organization_tag/1": {"name": "test", "color": "#000000"}})

    def test_delete_correct(self) -> None:
        response = self.request("organization_tag.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("organization_tag/1")

    def test_no_permission(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request("organization_tag.delete", {"id": 1})
        self.assert_status_code(response, 403)
        self.assertEqual(
            "You are not allowed to perform action organization_tag.delete. Missing OrganizationManagementLevel: can_manage_organization",
            response.json["message"],
        )

    def test_permission(self) -> None:
        self.base_permission_test(
            {},
            "organization_tag.delete",
            {"id": 1},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
        self.assert_model_not_exists("organization_tag/1")
