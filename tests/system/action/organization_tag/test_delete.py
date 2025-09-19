from tests.system.action.base import BaseActionTestCase


class OrganizationTagDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models({"organization_tag/1": {"name": "test", "color": "#000000"}})
        response = self.request("organization_tag.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("organization_tag/1")

    def test_no_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": "can_manage_users"},
                "organization_tag/1": {"name": "test", "color": "#000000"},
            }
        )
        response = self.request("organization_tag.delete", {"id": 1})
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action organization_tag.delete. Missing OrganizationManagementLevel: can_manage_organization"
            in response.json["message"]
        )

    def test_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": "can_manage_organization"},
                "organization_tag/1": {"name": "test", "color": "#000000"},
            }
        )
        response = self.request("organization_tag.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("organization_tag/1")
