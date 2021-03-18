from tests.system.action.base import BaseActionTestCase


class OrganisationUpdateActionTest(BaseActionTestCase):
    def test_update(self) -> None:
        self.create_model(
            "organisation/3", {"name": "aBuwxoYU", "description": "XrHbAWiF"}
        )
        response = self.request(
            "organisation.update",
            {"id": 3, "name": "testtest", "description": "blablabla"},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("organisation/3")
        assert model.get("name") == "testtest"
        assert model.get("description") == "blablabla"

    def test_update_some_more_fields(self) -> None:
        self.create_model(
            "organisation/3", {"name": "aBuwxoYU", "description": "XrHbAWiF"}
        )
        response = self.request(
            "organisation.update",
            {
                "id": 3,
                "name": "testtest",
                "description": "blablabla",
                "legal_notice": "GYjDABmD",
                "privacy_policy": "test1",
                "login_text": "test2",
                "theme": "test3",
                "custom_translations": "{}",
                "reset_password_verbose_errors": False,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("organisation/3")
        assert model.get("name") == "testtest"
        assert model.get("description") == "blablabla"
        assert model.get("legal_notice") == "GYjDABmD"
        assert model.get("privacy_policy") == "test1"
        assert model.get("login_text") == "test2"
        assert model.get("theme") == "test3"
        assert model.get("custom_translations") == "{}"
        assert model.get("reset_password_verbose_errors") is False

    def test_update_wrong_field(self) -> None:
        self.create_model(
            "organisation/3", {"name": "aBuwxoYU", "description": "XrHbAWiF"}
        )
        response = self.request(
            "organisation.update", {"id": 3, "wrong_name": "testtest"}
        )
        self.assert_status_code(response, 400)
        assert (
            "data must not contain {'wrong_name'} properties"
            in response.json["message"]
        )
        model = self.get_model("organisation/3")
        assert model.get("name") == "aBuwxoYU"
        assert model.get("description") == "XrHbAWiF"
