from textwrap import dedent

from psycopg.types.json import Jsonb

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class OrganizationUpdateActionTest(BaseActionTestCase):
    ListOfDicts = list[dict[str, str]]
    MeetingMappers = list[
        dict[str, str | ListOfDicts | dict[str, str | dict[str, str] | ListOfDicts]]
    ]
    saml_attr_mapping: dict[str, str | MeetingMappers] = {
        "saml_id": "username",
        "title": "title",
        "first_name": "firstName",
        "last_name": "lastName",
        "email": "email",
        "gender": "gender",
        "pronoun": "pronoun",
        "is_active": "is_active",
        "is_physical_person": "is_person",
        "member_number": "member_number",
    }

    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "theme/1": {"name": "default"},
                "theme/2": {"name": "default2"},
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
                "enable_anonymous": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            ONE_ORGANIZATION_FQID,
            {
                "name": "testtest",
                "description": "blablabla",
                "saml_attr_mapping": self.saml_attr_mapping,
                "enable_anonymous": True,
            },
        )

    def test_update_with_meeting(self) -> None:
        self.saml_attr_mapping.update(
            {
                "meeting_mappers": [
                    {
                        "name": "Mapper-Name",
                        "external_id": "Landtag",
                        "allow_update": "false",
                        "conditions": [
                            {"attribute": "membernumber", "condition": r"1426\d{4,6}$"},
                            {"attribute": "function", "condition": "board"},
                        ],
                        "mappings": {
                            "groups": [
                                {
                                    "attribute": "membership",
                                    "default": "admin, standard",
                                }
                            ],
                            "structure_levels": [
                                {
                                    "attribute": "ovname",
                                    "default": "struct1, struct2",
                                }
                            ],
                            "number": {"attribute": "p_number"},
                            "comment": {
                                "attribute": "idp_comment",
                                "default": "Group set via SSO",
                            },
                            "vote_weight": {
                                "attribute": "vote",
                                "default": "1.000000",
                            },
                            "present": {
                                "attribute": "present_key",
                                "default": "True",
                            },
                        },
                    }
                ]
            }
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

    def test_update_with_meeting_missing_ext_id(self) -> None:
        self.saml_attr_mapping.update(
            {"meeting_mappers": [{"external_idx": "Landtag"}]}
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
            "data.saml_attr_mapping.meeting_mappers[0] must contain ['external_id'] properties"
            in response.json["message"]
        )

    def test_update_with_meeting_wrong_attr(self) -> None:
        self.saml_attr_mapping.update(
            {"meeting_mappers": [{"external_id": "Landtag", "unknown_field": " "}]}
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
            "data.saml_attr_mapping.meeting_mappers[0] must not contain {'unknown_field'} properties"
            in response.json["message"]
        )

        self.saml_attr_mapping.update(
            {
                "meeting_mappers": [
                    {"external_id": "Landtag", "mappings": {"unknown_field": " "}}
                ]
            }
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
            "data.saml_attr_mapping.meeting_mappers[0].mappings must not contain {'unknown_field'} properties"
            in response.json["message"]
        )

        self.saml_attr_mapping.update(
            {
                "meeting_mappers": [
                    {
                        "external_id": "Landtag",
                        "mappings": {"vote_weight": {"unknown_field": " "}},
                    }
                ]
            }
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
            "data.saml_attr_mapping.meeting_mappers[0].mappings.vote_weight must not contain {'unknown_field'} properties"
            in response.json["message"]
        )

        self.saml_attr_mapping.update(
            {
                "meeting_mappers": [
                    {
                        "external_id": "Landtag",
                        "mappings": {"groups": [{"unknown_field": " "}]},
                    }
                ]
            }
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
            "data.saml_attr_mapping.meeting_mappers[0].mappings.groups[0] must not contain {'unknown_field'} properties"
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
                "disable_forward_with_attachments": True,
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
                "disable_forward_with_attachments": True,
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
                    "saml_attr_mapping": Jsonb(self.saml_attr_mapping),
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
                "name": "OpenSlides Organization",
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
            ONE_ORGANIZATION_FQID,
            {"name": "OpenSlides Organization", "description": None},
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
            response = self.request("organization.update", {"id": 1, field: value})
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
        for id_ in (1, 4, 7):
            self.create_meeting(id_)
        response = self.request(
            "organization.update",
            {"id": 1, "limit_of_meetings": 2},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Your organization has 3 active meetings. You cannot set the limit lower.",
            response.json["message"],
        )

    def test_update_too_many_active_users(self) -> None:
        self.create_user("violetta")
        self.create_user("banafshe")
        response = self.request(
            "organization.update",
            {"id": 1, "limit_of_users": 2},
        )
        self.assert_status_code(response, 400)
        assert (
            "Active users: 3. You cannot set the limit lower."
            == response.json["message"]
        )
