from textwrap import dedent

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class OrganizationUpdateActionTest(BaseActionTestCase):
    saml_attr_mapping: dict[str, str | dict[str, str]] = {
        "saml_id": "username",
        "title": "title",
        "first_name": "firstName",
        "last_name": "lastName",
        "email": "email",
        "gender": "gender",
        "pronoun": "pronoun",
        "is_active": "is_active",
        "is_physical_person": "is_person",
    }

    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "name": "aBuwxoYU",
                    "description": "XrHbAWiF",
                    "theme_id": 1,
                    "theme_ids": [1, 2],
                },
                "theme/1": {
                    "name": "default",
                    "organization_id": 1,
                    "theme_for_organization_id": 1,
                },
                "theme/2": {
                    "name": "default2",
                    "organization_id": 1,
                },
            }
        )

    def test_update(self) -> None:
        response = self.request(
            "organization.update",
            {
                "id": 1,
                "name": "testtest",
                "description": "blablabla",
                "saml_attr_mapping": self.saml_attr_mapping,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            ONE_ORGANIZATION_FQID,
            {
                "name": "testtest",
                "description": "blablabla",
                "saml_attr_mapping": self.saml_attr_mapping,
            },
        )

    def test_update_with_meeting(self) -> None:
        self.saml_attr_mapping.update(
            {"meeting": {"external_id": "Landtag", "external_group_id": "Delegated"}}
        ),
        response = self.request(
            "organization.update",
            {
                "id": 1,
                "name": "testtest",
                "description": "blablabla",
                "saml_attr_mapping": self.saml_attr_mapping,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            ONE_ORGANIZATION_FQID,
            {
                "name": "testtest",
                "description": "blablabla",
                "saml_attr_mapping": self.saml_attr_mapping,
            },
        )

    def test_update_with_meeting_error(self) -> None:
        self.saml_attr_mapping.update(
            {"meeting": {"external_idx": "Landtag", "external_group_id": "Delegated"}}
        ),
        response = self.request(
            "organization.update",
            {
                "id": 1,
                "name": "testtest",
                "description": "blablabla",
                "saml_attr_mapping": self.saml_attr_mapping,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "data.saml_attr_mapping.meeting must not contain {'external_idx'} properties"
            in response.json["message"]
        )

    def test_update_some_more_fields(self) -> None:
        response = self.request(
            "organization.update",
            {
                "id": 1,
                "name": "testtest",
                "description": "blablabla",
                "legal_notice": "GYjDABmD",
                "privacy_policy": "test1",
                "login_text": "test2",
                "theme_id": 2,
                "reset_password_verbose_errors": False,
                "enable_chat": True,
                "url": "https://openslides.example.com",
                "users_email_sender": "email_sender",
                "users_email_replyto": " email@replyto.de  ",
                "users_email_subject": "email subject",
                "users_email_body": "Dear {name},\n\nthis is your personal OpenSlides login:\n\n{url}\nUsername: {username}\nPassword: {password}\n\n\nThis email was generated automatically.",
                "require_duplicate_from": True,
                "saml_enabled": True,
                "saml_login_button_text": "Text for SAML login button",
                "saml_attr_mapping": self.saml_attr_mapping,
                "saml_metadata_idp": dedent(
                    """
                    <md:EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
                        xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                        xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
                        entityID="https://auth.digiv.de/auth/realms/demo">
                        </md:IDPSSODescriptor>
                    </md:EntityDescriptor>
                    """
                ),
                "saml_metadata_sp": dedent(
                    """
                    <EntityDescriptor
                    xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                    xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
                    entityID="http://localhost:9004/saml/metadata">
                    </EntityDescriptor>
                    """
                ),
                "saml_private_key": "private key dependency",
                "genders": ["male", "female", "rabbit"],
            },
        )
        self.assert_status_code(response, 200)
        organization = self.assert_model_exists(
            ONE_ORGANIZATION_FQID,
            {
                "name": "testtest",
                "description": "blablabla",
                "legal_notice": "GYjDABmD",
                "privacy_policy": "test1",
                "login_text": "test2",
                "theme_id": 2,
                "theme_ids": [1, 2],
                "reset_password_verbose_errors": False,
                "enable_chat": True,
                "url": "https://openslides.example.com",
                "users_email_sender": "email_sender",
                "users_email_replyto": "email@replyto.de",
                "users_email_subject": "email subject",
                "users_email_body": "Dear {name},\n\nthis is your personal OpenSlides login:\n\n{url}\nUsername: {username}\nPassword: {password}\n\n\nThis email was generated automatically.",
                "require_duplicate_from": True,
                "saml_enabled": True,
                "saml_login_button_text": "Text for SAML login button",
                "saml_attr_mapping": self.saml_attr_mapping,
                "saml_private_key": "private key dependency",
                "genders": ["male", "female", "rabbit"],
            },
        )
        assert (
            'xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"'
            in organization["saml_metadata_idp"]
        )
        assert "http://www.w3.org/2000/09/xmldsig#" in organization["saml_metadata_sp"]

        self.assert_model_exists(
            "theme/1", {"organization_id": 1, "theme_for_organization_id": None}
        )
        self.assert_model_exists(
            "theme/2", {"organization_id": 1, "theme_for_organization_id": 1}
        )

    def test_update_remove_saml_configuration(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "saml_enabled": True,
                    "saml_attr_mapping": self.saml_attr_mapping,
                    "saml_metadata_idp": dedent(
                        """
                    <md:EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
                        xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                        xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
                        entityID="https://auth.digiv.de/auth/realms/demo">
                        </md:IDPSSODescriptor>
                    </md:EntityDescriptor>
                    """
                    ),
                    "saml_metadata_sp": dedent(
                        """
                    <EntityDescriptor
                    xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                    xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
                    entityID="http://localhost:9004/saml/metadata">
                    </EntityDescriptor>
                    """
                    ),
                    "saml_private_key": "private key dependency",
                }
            }
        )
        response = self.request(
            "organization.update",
            {
                "id": 1,
                "saml_enabled": False,
                "saml_attr_mapping": None,
                "saml_metadata_idp": "",
                "saml_metadata_sp": None,
                "saml_private_key": "",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            ONE_ORGANIZATION_FQID,
            {
                "name": "aBuwxoYU",
                "saml_enabled": False,
                "saml_attr_mapping": None,
                "saml_metadata_idp": "",
                "saml_metadata_sp": None,
                "saml_private_key": "",
            },
        )

    def test_update_wrong_field(self) -> None:
        response = self.request(
            "organization.update", {"id": 1, "wrong_name": "testtest"}
        )
        self.assert_status_code(response, 400)
        assert (
            "data must not contain {'wrong_name'} properties"
            in response.json["message"]
        )
        self.assert_model_exists(
            ONE_ORGANIZATION_FQID, {"name": "aBuwxoYU", "description": "XrHbAWiF"}
        )

    def test_update_broken_email(self) -> None:
        response = self.request(
            "organization.update", {"id": 1, "users_email_replyto": "broken@@"}
        )
        self.assert_status_code(response, 400)
        assert "users_email_replyto must be valid email." in response.json["message"]

    def test_update_broken_email_sender(self) -> None:
        response = self.request(
            "organization.update", {"id": 1, "users_email_sender": "broken\\"}
        )
        self.assert_status_code(response, 400)
        assert (
            "users_email_sender must not contain '[', ']', '\\'."
            in response.json["message"]
        )

    def test_update_broken_saml_attr_mapping_string(self) -> None:
        response = self.request(
            "organization.update",
            {
                "id": 1,
                "saml_attr_mapping": "This is not a valid JSON formated sso-configuration",
            },
        )
        self.assert_status_code(response, 400)
        assert "data.saml_attr_mapping must be object" in response.json["message"]

    def test_update_broken_saml_attr_mapping_array(self) -> None:
        response = self.request(
            "organization.update", {"id": 1, "saml_attr_mapping": ["f1", "f2"]}
        )
        self.assert_status_code(response, 400)
        assert "data.saml_attr_mapping must be object" in response.json["message"]

    def test_update_broken_saml_attr_mapping_missing_saml_id(self) -> None:
        response = self.request(
            "organization.update", {"id": 1, "saml_attr_mapping": {"x": "y"}}
        )
        self.assert_status_code(response, 400)
        assert (
            "data.saml_attr_mapping must contain ['saml_id'] properties"
            in response.json["message"]
        )

    def test_update_broken_saml_attr_mapping_unknown_field(self) -> None:
        response = self.request(
            "organization.update",
            {"id": 1, "saml_attr_mapping": {"saml_id": "111", "unkown_field": "xxx"}},
        )
        self.assert_status_code(response, 400)
        assert (
            "data.saml_attr_mapping must not contain {'unkown_field'} properties"
            in response.json["message"]
        )

    def test_update_default_language(self) -> None:
        response = self.request(
            "organization.update", {"id": 1, "default_language": "it"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"default_language": "it"})

    def test_update_genders_remove(self) -> None:
        self.set_models(
            {
                "organization/1": {"genders": ["male", "female", "test"]},
                "user/6": {"username": "with_test_gender", "gender": "test"},
                "user/7": {"username": "not_changed", "gender": "male"},
            }
        )
        response = self.request(
            "organization.update", {"id": 1, "genders": ["male", "female"]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"genders": ["male", "female"]})
        self.assert_model_exists(
            "user/6", {"username": "with_test_gender", "gender": None}
        )
        self.assert_model_exists(
            "user/7", {"username": "not_changed", "gender": "male"}
        )

    def test_update_genders_empty(self) -> None:
        self.set_models(
            {
                "organization/1": {"genders": ["male", "female", "test"]},
                "user/6": {"gender": "test"},
                "user/7": {"gender": "male"},
            }
        )
        response = self.request("organization.update", {"id": 1, "genders": []})
        self.assert_status_code(response, 200)
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"genders": []})
        self.assert_model_exists("user/6", {"gender": None})
        self.assert_model_exists("user/7", {"gender": None})

    def test_update_group_a_no_permissions(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request("organization.update", {"id": 1, "name": "blablabla"})
        self.assert_status_code(response, 403)

    def test_update_group_a_permissions(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        response = self.request("organization.update", {"id": 1, "name": "blablabla"})
        self.assert_status_code(response, 200)

    def test_update_group_b_no_permissions(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        fields = {
            "reset_password_verbose_errors": True,
            "enable_electronic_voting": True,
            "limit_of_meetings": 2,
            "limit_of_users": 1,
            "url": "test",
        }
        for field, value in fields.items():
            response = self.request(
                "organization.update",
                {
                    "id": 1,
                    field: value,
                },
            )
            self.assert_status_code(response, 403)

    def test_update_group_b_permissions(self) -> None:
        response = self.request(
            "organization.update",
            {
                "id": 1,
                "reset_password_verbose_errors": True,
                "enable_electronic_voting": True,
                "limit_of_meetings": 2,
                "limit_of_users": 1,
                "url": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            ONE_ORGANIZATION_FQID,
            {"limit_of_meetings": 2, "limit_of_users": 1, "url": "test"},
        )

    def test_update_too_many_active_meetings(self) -> None:
        self.update_model(
            ONE_ORGANIZATION_FQID,
            {
                "active_meeting_ids": [1, 2, 3],
            },
        )
        response = self.request(
            "organization.update",
            {
                "id": 1,
                "limit_of_meetings": 2,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Your organization has 3 active meetings. You cannot set the limit lower.",
            response.json["message"],
        )

    def test_update_too_many_active_users(self) -> None:
        self.set_models(
            {
                "user/2": {"is_active": True},
                "user/3": {"is_active": True},
            }
        )
        response = self.request(
            "organization.update",
            {
                "id": 1,
                "limit_of_users": 2,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Active users: 3. You cannot set the limit lower."
            == response.json["message"]
        )
