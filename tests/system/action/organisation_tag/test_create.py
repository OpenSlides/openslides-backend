from tests.system.action.base import BaseActionTestCase


class OrganisationTagCreate(BaseActionTestCase):
    def test_create(self) -> None:
        response = self.request(
            "organisation_tag.create", {"name": "wSvQHymN", "color": "#eeeeee"}
        )
        self.assert_status_code(response, 200)
        organisation_tag = self.get_model("organisation_tag/1")
        assert organisation_tag.get("name") == "wSvQHymN"
        assert organisation_tag.get("color") == "#eeeeee"

    def test_create_empty_data(self) -> None:
        response = self.request("organisation_tag.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['name', 'color'] properties",
            response.json["message"],
        )

    def test_no_permission(self) -> None:
        self.set_models(
            {"user/1": {"organisation_management_level": "can_manage_users"}}
        )
        response = self.request(
            "organisation_tag.create", {"name": "wSvQHymN", "color": "#eeeeee"}
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action organisation_tag.create. Missing Organisation Management Level: can_manage_organisation"
            in response.json["message"]
        )

    def test_permission(self) -> None:
        self.set_models(
            {"user/1": {"organisation_management_level": "can_manage_organisation"}}
        )
        response = self.request(
            "organisation_tag.create", {"name": "wSvQHymN", "color": "#eeeeee"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("organisation_tag/1")
