from tests.system.action.base import BaseActionTestCase


class OrganisationTagUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models({"organisation_tag/1": {"name": "old", "color": "#000000"}})
        response = self.request(
            "organisation_tag.update", {"id": 1, "name": "test", "color": "#121212"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "organisation_tag/1", {"name": "test", "color": "#121212"}
        )

    def test_no_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organisation_management_level": "can_manage_users"},
                "organisation_tag/1": {"name": "test", "color": "#000000"},
            }
        )
        response = self.request(
            "organisation_tag.update", {"id": 1, "name": "test", "color": "#121212"}
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action organisation_tag.update. Missing OrganisationManagementLevel: can_manage_organisation"
            in response.json["message"]
        )

    def test_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organisation_management_level": "can_manage_organisation"},
                "organisation_tag/1": {"name": "old", "color": "#000000"},
            }
        )
        response = self.request(
            "organisation_tag.update", {"id": 1, "name": "test", "color": "#121212"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "organisation_tag/1", {"name": "test", "color": "#121212"}
        )
