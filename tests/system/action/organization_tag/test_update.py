from tests.system.action.base import BaseActionTestCase


class OrganizationTagUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models({"organization_tag/1": {"name": "old", "color": "#000000"}})
        response = self.request(
            "organization_tag.update", {"id": 1, "name": "test", "color": "#121212"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "organization_tag/1", {"name": "test", "color": "#121212"}
        )

    def test_no_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": "can_manage_users"},
                "organization_tag/1": {"name": "test", "color": "#000000"},
            }
        )
        response = self.request(
            "organization_tag.update", {"id": 1, "name": "test", "color": "#121212"}
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action organization_tag.update. Missing OrganizationManagementLevel: can_manage_organization"
            in response.json["message"]
        )

    def test_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": "can_manage_organization"},
                "organization_tag/1": {"name": "old", "color": "#000000"},
            }
        )
        response = self.request(
            "organization_tag.update", {"id": 1, "name": "test", "color": "#121212"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "organization_tag/1", {"name": "test", "color": "#121212"}
        )
