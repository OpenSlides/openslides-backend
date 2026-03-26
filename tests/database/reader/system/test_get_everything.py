from unittest.mock import MagicMock

from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from tests.database.reader.system.util import (
    setup_data,
    standard_data,
    standard_responses,
)


def test_simple(db_connection: Connection) -> None:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get_everything()
    assert response == standard_responses | {
        "organization": {
            1: {
                "active_meeting_ids": None,
                "archived_meeting_ids": None,
                "committee_ids": [
                    1,
                    2,
                ],
                "default_language": "en",
                "description": None,
                "disable_forward_with_attachments": None,
                "enable_anonymous": None,
                "enable_chat": None,
                "enable_electronic_voting": None,
                "gender_ids": None,
                "id": 1,
                "legal_notice": None,
                "limit_of_meetings": 0,
                "limit_of_users": 0,
                "login_text": None,
                "mediafile_ids": None,
                "name": "OpenSlides Organization",
                "organization_tag_ids": None,
                "privacy_policy": None,
                "published_mediafile_ids": None,
                "require_duplicate_from": None,
                "reset_password_verbose_errors": None,
                "restrict_edit_forward_committees": None,
                "restrict_editing_same_level_committee_admins": None,
                "saml_attr_mapping": None,
                "saml_enabled": None,
                "saml_login_button_text": "SAML login",
                "saml_metadata_idp": None,
                "saml_metadata_sp": None,
                "saml_private_key": None,
                "template_meeting_ids": None,
                "theme_id": 1,
                "theme_ids": [
                    1,
                ],
                "url": "https://example.com",
                "user_ids": [
                    1,
                    2,
                    3,
                ],
                "users_email_body": "Dear {name},\n"
                "\n"
                "this is your personal OpenSlides login:\n"
                "\n"
                "{url}\n"
                "Username: {username}\n"
                "Password: {password}\n"
                "\n"
                "\n"
                "This email was generated automatically.",
                "users_email_replyto": None,
                "users_email_sender": "OpenSlides",
                "users_email_subject": "OpenSlides access data",
            },
        },
        "theme": {
            1: {
                "abstain": None,
                "accent_100": None,
                "accent_200": None,
                "accent_300": None,
                "accent_400": None,
                "accent_50": None,
                "accent_500": "#2196f3",
                "accent_600": None,
                "accent_700": None,
                "accent_800": None,
                "accent_900": None,
                "accent_a100": None,
                "accent_a200": None,
                "accent_a400": None,
                "accent_a700": None,
                "headbar": None,
                "id": 1,
                "name": "OpenSlides Organization",
                "no": None,
                "organization_id": 1,
                "primary_100": None,
                "primary_200": None,
                "primary_300": None,
                "primary_400": None,
                "primary_50": None,
                "primary_500": "#317796",
                "primary_600": None,
                "primary_700": None,
                "primary_800": None,
                "primary_900": None,
                "primary_a100": None,
                "primary_a200": None,
                "primary_a400": None,
                "primary_a700": None,
                "theme_for_organization_id": 1,
                "warn_100": None,
                "warn_200": None,
                "warn_300": None,
                "warn_400": None,
                "warn_50": None,
                "warn_500": "#f06400",
                "warn_600": None,
                "warn_700": None,
                "warn_800": None,
                "warn_900": None,
                "warn_a100": None,
                "warn_a200": None,
                "warn_a400": None,
                "warn_a700": None,
                "yes": None,
            },
        },
    }
