from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class OrganizationUpdateActionTest(BaseActionTestCase):
    def test_update(self) -> None:
        self.create_model(
            "organization/3", {"name": "aBuwxoYU", "description": "XrHbAWiF"}
        )
        response = self.request(
            "organization.update",
            {"id": 3, "name": "testtest", "description": "blablabla"},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("organization/3")
        assert model.get("name") == "testtest"
        assert model.get("description") == "blablabla"

    def test_update_some_more_fields(self) -> None:
        self.create_model(
            "organization/3", {"name": "aBuwxoYU", "description": "XrHbAWiF"}
        )
        response = self.request(
            "organization.update",
            {
                "id": 3,
                "name": "testtest",
                "description": "blablabla",
                "legal_notice": "GYjDABmD",
                "privacy_policy": "test1",
                "login_text": "test2",
                "theme": "test3",
                "custom_translations": {},
                "reset_password_verbose_errors": False,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("organization/3")
        assert model.get("name") == "testtest"
        assert model.get("description") == "blablabla"
        assert model.get("legal_notice") == "GYjDABmD"
        assert model.get("privacy_policy") == "test1"
        assert model.get("login_text") == "test2"
        assert model.get("theme") == "test3"
        assert model.get("custom_translations") == {}
        assert model.get("reset_password_verbose_errors") is False

    def test_update_wrong_field(self) -> None:
        self.create_model(
            "organization/3", {"name": "aBuwxoYU", "description": "XrHbAWiF"}
        )
        response = self.request(
            "organization.update", {"id": 3, "wrong_name": "testtest"}
        )
        self.assert_status_code(response, 400)
        assert (
            "data must not contain {'wrong_name'} properties"
            in response.json["message"]
        )
        model = self.get_model("organization/3")
        assert model.get("name") == "aBuwxoYU"
        assert model.get("description") == "XrHbAWiF"

    def test_update_group_a_no_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                },
                "organization/3": {"name": "aBuwxoYU", "description": "XrHbAWiF"},
            }
        )
        response = self.request("organization.update", {"id": 3, "name": "blablabla"})
        self.assert_status_code(response, 403)

    def test_update_group_a_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
                "organization/3": {"name": "aBuwxoYU", "description": "XrHbAWiF"},
            }
        )
        response = self.request("organization.update", {"id": 3, "name": "blablabla"})
        self.assert_status_code(response, 200)

    def test_update_group_b_no_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
                "organization/3": {"name": "aBuwxoYU", "description": "XrHbAWiF"},
            }
        )
        response = self.request(
            "organization.update",
            {
                "id": 3,
                "reset_password_verbose_errors": True,
                "enable_electronic_voting": True,
            },
        )
        self.assert_status_code(response, 403)

    def test_update_group_b_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.SUPERADMIN
                },
                "organization/3": {"name": "aBuwxoYU", "description": "XrHbAWiF"},
            }
        )
        response = self.request(
            "organization.update",
            {
                "id": 3,
                "reset_password_verbose_errors": True,
                "enable_electronic_voting": True,
            },
        )
        self.assert_status_code(response, 200)
