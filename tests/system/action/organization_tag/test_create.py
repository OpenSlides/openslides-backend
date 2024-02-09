from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class OrganizationTagCreate(BaseActionTestCase):
    def test_create(self) -> None:
        response = self.request(
            "organization_tag.create",
            {"name": "wSvQHymN", "color": "#eeeeee", "organization_id": 1},
        )
        self.assert_status_code(response, 200)
        organization_tag = self.get_model("organization_tag/1")
        assert organization_tag.get("name") == "wSvQHymN"
        assert organization_tag.get("color") == "#eeeeee"
        assert organization_tag.get("organization_id") == 1
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"organization_tag_ids": [1]})

    def test_create_empty_data(self) -> None:
        response = self.request("organization_tag.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['color', 'name', 'organization_id'] properties",
            response.json["message"],
        )

    def test_no_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": "can_manage_users"},
            }
        )
        response = self.request(
            "organization_tag.create",
            {"name": "wSvQHymN", "color": "#eeeeee", "organization_id": 1},
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action organization_tag.create. Missing OrganizationManagementLevel: can_manage_organization"
            in response.json["message"]
        )

    def test_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": "can_manage_organization"},
            }
        )
        response = self.request(
            "organization_tag.create",
            {"name": "wSvQHymN", "color": "#eeeeee", "organization_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("organization_tag/1")
