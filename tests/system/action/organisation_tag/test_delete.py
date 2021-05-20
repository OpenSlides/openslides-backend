from tests.system.action.base import BaseActionTestCase


class OrganisationTagDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models({"organisation_tag/1": {"name": "test", "color": "#000000"}})
        response = self.request("organisation_tag.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("organisation_tag/1")

    def test_no_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organisation_management_level": "can_manage_users"},
                "organisation_tag/1": {"name": "test", "color": "#000000"},
            }
        )
        response = self.request("organisation_tag.delete", {"id": 1})
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action organisation_tag.delete. Missing OrganisationManagementLevel: can_manage_organisation"
            in response.json["message"]
        )

    def test_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organisation_management_level": "can_manage_organisation"},
                "organisation_tag/1": {"name": "test", "color": "#000000"},
            }
        )
        response = self.request("organisation_tag.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("organisation_tag/1")
