from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class OrganizationTagCreate(BaseActionTestCase):
    def test_create(self) -> None:
        response = self.request(
            "organization_tag.create",
            {"name": "wSvQHymN", "color": "#eeeeee", "organization_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "organization_tag/1",
            {"name": "wSvQHymN", "color": "#eeeeee", "organization_id": 1},
        )
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"organization_tag_ids": [1]})

    def test_create_empty_data(self) -> None:
        response = self.request("organization_tag.create", {})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action organization_tag.create: data must contain ['color', 'name', 'organization_id'] properties",
            response.json["message"],
        )

    def test_no_permission(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request(
            "organization_tag.create",
            {"name": "wSvQHymN", "color": "#eeeeee", "organization_id": 1},
        )
        self.assert_status_code(response, 403)
        self.assertEqual(
            "You are not allowed to perform action organization_tag.create. Missing OrganizationManagementLevel: can_manage_organization",
            response.json["message"],
        )

    def test_permission(self) -> None:
        self.base_permission_test(
            {},
            "organization_tag.create",
            {"name": "wSvQHymN", "color": "#eeeeee", "organization_id": 1},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
        self.assert_model_exists("organization_tag/1")
