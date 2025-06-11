from time import time

from openslides_backend.action.actions.user.send_invitation_email import EmailErrorType
from openslides_backend.action.mixins.send_email_mixin import EmailSettings
from openslides_backend.permissions.permissions import Permission, Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase
from tests.system.action.mail_base import (
    AIOHandler,
    AiosmtpdServerManager,
    set_test_email_settings,
)


class SendInvitationMail(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "url": "https://example.com",
                },
                "meeting/1": {
                    "name": "annual general meeting",
                    "users_email_sender": "Openslides",
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [2],
                },
                "user/2": {
                    "username": "Testuser 2",
                    "first_name": "Jim",
                    "last_name": "Beam",
                    "default_password": "secret",
                    "email": "recipient2@example.com",
                    "meeting_user_ids": [2],
                    "meeting_ids": [1],
                },
                "meeting_user/2": {
                    "meeting_id": 1,
                    "user_id": 2,
                    "group_ids": [1],
                },
            },
        )
        # important to reset all these settings
        set_test_email_settings()

    def test_send_correct(self) -> None:
        start_time = int(time())
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                    "meeting_id": 1,
                },
            )
        self.assert_status_code(response, 200)
        user = self.get_model("user/2")
        last_email_sent = user.get("last_email_sent", 0)
        self.assertGreaterEqual(last_email_sent, start_time)

    def test_send_mixed_multimail(self) -> None:
        """
        Test with 2 PayloadElements and some actions
        There are correct and falsy actions, look at user name below,
        except user/2 => mail is sent and
               user/8, which doesn't exist
        """
        self.create_meeting(4)
        self.set_models(
            {
                "user/3": {
                    "username": "Testuser 3 no email",
                    "first_name": "Jim3",
                    "email": "",
                    "meeting_user_ids": [13],
                    "meeting_ids": [1],
                },
                "user/4": {
                    "username": "Testuser 4 falsy email",
                    "first_name": "Jim4",
                    "email": "recipient4",
                    "meeting_user_ids": [14],
                    "meeting_ids": [1],
                },
                "user/5": {
                    "username": "Testuser 5 wrong meeting",
                    "first_name": "Jim5",
                    "email": "recipient5@example.com",
                    "meeting_user_ids": [15],
                    "meeting_ids": [1],
                },
                "user/6": {
                    "username": "Testuser 6 wrong schema",
                    "first_name": "Jim6",
                    "email": "recipient6@example.com",
                    "meeting_user_ids": [16],
                    "meeting_ids": [1],
                },
                "user/7": {
                    "username": "Testuser 7 special email for server detection",
                    "first_name": "Jim7",
                    "email": "recipient7_create_error551@example.com",
                    "meeting_user_ids": [17],
                    "meeting_ids": [1],
                },
                "meeting_user/13": {
                    "meeting_id": 1,
                    "user_id": 3,
                    "group_ids": [1],
                },
                "meeting_user/14": {
                    "meeting_id": 1,
                    "user_id": 4,
                    "group_ids": [1],
                },
                "meeting_user/15": {
                    "meeting_id": 1,
                    "user_id": 5,
                    "group_ids": [1],
                },
                "meeting_user/16": {
                    "meeting_id": 1,
                    "user_id": 6,
                    "group_ids": [1],
                },
                "meeting_user/17": {
                    "meeting_id": 1,
                    "user_id": 7,
                    "group_ids": [1],
                },
            },
        )

        start_time = int(time())
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request_json(
                [
                    {
                        "action": "user.send_invitation_email",
                        "data": [
                            {"id": 2, "meeting_id": 1},
                            {"id": 3, "meeting_id": 1},
                        ],
                    },
                    {
                        "action": "user.send_invitation_email",
                        "data": [
                            {"id": 4, "meeting_id": 1},
                            {"id": 5, "meeting_id": 4},
                            {"id": 6, "meeting_id": "1"},
                            {"id": 7, "meeting_id": 1},
                            {"id": 8, "meeting_id": 1},
                        ],
                    },
                ]
            )

        self.assert_status_code(response, 200)
        user2 = self.get_model("user/2")
        self.assertGreaterEqual(user2.get("last_email_sent", 0), start_time)
        for i in range(3, 8, 1):
            self.assert_model_exists(f"user/{i}", {"last_email_sent": None})
        self.assertEqual(response.json["results"][0][0]["sent"], True)
        self.assertEqual(
            response.json["results"][0][0]["recipient"], "recipient2@example.com"
        )
        self.assertEqual(response.json["results"][0][0]["recipient_user_id"], 2)

        self.assertEqual(response.json["results"][0][1]["sent"], False)
        self.assertEqual(response.json["results"][0][1]["recipient_user_id"], 3)
        self.assertEqual(
            response.json["results"][0][1]["type"], EmailErrorType.USER_ERROR
        )
        self.assertIn(
            "'Testuser 3 no email' has no email address.",
            response.json["results"][0][1]["message"],
        )

        self.assertEqual(response.json["results"][1][0]["sent"], False)
        self.assertEqual(response.json["results"][1][0]["recipient_user_id"], 4)
        self.assertEqual(
            response.json["results"][1][0]["type"], EmailErrorType.USER_ERROR
        )
        self.assertIn(
            "'Testuser 4 falsy email' has no valid email address.",
            response.json["results"][1][0]["message"],
        )

        self.assertEqual(response.json["results"][1][1]["sent"], False)
        self.assertEqual(response.json["results"][1][1]["recipient_user_id"], 5)
        self.assertEqual(
            response.json["results"][1][1]["type"], EmailErrorType.USER_ERROR
        )
        self.assertIn(
            "'Testuser 5 wrong meeting' does not belong to meeting/4",
            response.json["results"][1][1]["message"],
        )

        self.assertEqual(response.json["results"][1][2]["sent"], False)
        self.assertEqual(response.json["results"][1][2]["recipient_user_id"], 6)
        self.assertEqual(
            response.json["results"][1][2]["type"], EmailErrorType.OTHER_ERROR
        )
        self.assertIn(
            "JsonSchema: data.meeting_id must be integer",
            response.json["results"][1][2]["message"],
        )

        self.assertEqual(response.json["results"][1][3]["sent"], False)
        self.assertEqual(response.json["results"][1][3]["recipient_user_id"], 7)
        self.assertEqual(
            response.json["results"][1][3]["type"], EmailErrorType.CONFIGURATION_ERROR
        )
        self.assertIn(
            "SMTPRecipientsRefused: {'recipient7_create_error551@example.com': (551, b'invalid eMail address from server')}",
            response.json["results"][1][3]["message"],
        )

        self.assert_model_not_exists("user/8")
        self.assertEqual(response.json["results"][1][4]["sent"], False)
        self.assertEqual(response.json["results"][1][4]["recipient_user_id"], 8)
        self.assertEqual(
            response.json["results"][1][4]["type"], EmailErrorType.OTHER_ERROR
        )
        self.assertIn(
            "DatabaseException:  Model 'user/8' does not exist.",
            response.json["results"][1][4]["message"],
        )

    def test_SMTPAuthentificationError_wrong_password(self) -> None:
        EmailSettings.password = "not secret"
        EmailSettings.user = "sender@example.com"

        handler = AIOHandler()
        with AiosmtpdServerManager(handler, auth=True):
            response = self.request(
                "user.send_invitation_email",
                {},
            )
        self.assert_status_code(response, 200)
        self.assertEqual(
            response.json["results"][0][0]["type"], EmailErrorType.CONFIGURATION_ERROR
        )
        self.assertIn(
            "SMTPAuthenticationError: (535, b'5.7.8 Authentication credentials invalid')",
            response.json["results"][0][0]["message"],
        )

    def test_SMTPSenderRefused_not_authenticated(self) -> None:
        handler = AIOHandler()
        with AiosmtpdServerManager(handler, auth=True):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                    "meeting_id": 1,
                },
            )
        self.assert_status_code(response, 200)
        self.assertEqual(
            response.json["results"][0][0]["type"], EmailErrorType.CONFIGURATION_ERROR
        )
        self.assertIn(
            f"SMTPSenderRefused: (530, b'5.7.0 Authentication required', '{EmailSettings.default_from_email}')",
            response.json["results"][0][0]["message"],
        )

    def test_ConnectionRefusedError_wrong_port(self) -> None:
        EmailSettings.timeout = 1
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            EmailSettings.port = 26
            response = self.request(
                "user.send_invitation_email",
                {},
            )
        self.assert_status_code(response, 200)
        self.assertEqual(
            response.json["results"][0][0]["type"], EmailErrorType.CONFIGURATION_ERROR
        )
        self.assertIn(
            "ConnectionRefusedError: [Errno 111] Connection refused",
            response.json["results"][0][0]["message"],
        )

    def test_SSLCertVerificationError_self_signed(self) -> None:
        EmailSettings.connection_security = "STARTTLS"
        EmailSettings.port = 587
        EmailSettings.accept_self_signed_certificate = False

        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {},
            )
        self.assert_status_code(response, 200)
        self.assertEqual(
            response.json["results"][0][0]["type"], EmailErrorType.CONFIGURATION_ERROR
        )
        self.assertIn(
            "SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate",
            response.json["results"][0][0]["message"],
        )

    # Tests regarding sender name
    def test_sender_without_sender_name(self) -> None:
        self.set_models(
            {"meeting/1": {"users_email_sender": ""}},
        )
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                    "meeting_id": 1,
                },
            )
        self.assert_status_code(response, 200)
        self.assertEqual(response.json["results"][0][0]["sent"], True)
        self.assertEqual(
            response.json["results"][0][0]["recipient"], "recipient2@example.com"
        )
        self.assertEqual(response.json["results"][0][0]["recipient_user_id"], 2)
        self.assertEqual(handler.emails[0]["from"], EmailSettings.default_from_email)
        self.assertIn(
            f"From: {EmailSettings.default_from_email}",
            handler.emails[0]["data"],
        )

    def test_sender_with_sender_name(self) -> None:
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                    "meeting_id": 1,
                },
            )
        self.assert_status_code(response, 200)
        self.assertEqual(response.json["results"][0][0]["sent"], True)
        self.assertEqual(
            response.json["results"][0][0]["recipient"], "recipient2@example.com"
        )
        meeting = self.get_model("meeting/1")
        self.assertEqual(response.json["results"][0][0]["recipient_user_id"], 2)
        self.assertEqual(handler.emails[0]["from"], EmailSettings.default_from_email)
        self.assertIn(
            f"From: {meeting.get('users_email_sender')} <{EmailSettings.default_from_email}>",
            handler.emails[0]["data"],
        )

    def test_sender_with_wrong_sender(self) -> None:
        EmailSettings.default_from_email = "wrong_sender@email"
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {},
            )
        self.assert_status_code(response, 200)
        self.assertEqual(response.json["results"][0][0]["sent"], False)
        self.assertEqual(
            response.json["results"][0][0]["type"], EmailErrorType.CONFIGURATION_ERROR
        )
        self.assertEqual(len(handler.emails), 0)
        self.assertIn(
            "email wrong_sender@email is not a valid sender email address.",
            response.json["results"][0][0]["message"],
        )

    def test_sender_with_wrong_sender_name(self) -> None:
        """wrong name in meeting 1, but okay in meeting 4"""
        self.create_meeting(4)
        self.set_models(
            {
                "meeting/1": {"users_email_sender": "x]x"},
                "meeting/4": {"users_email_sender": "Openslides"},
                "user/3": {
                    "username": "Testuser 3",
                    "first_name": "Jim3",
                    "email": "x@abc.com",
                    "meeting_user_ids": [13, 14],
                    "meeting_ids": [1, 4],
                },
                "meeting_user/13": {
                    "meeting_id": 1,
                    "user_id": 3,
                    "group_ids": [1],
                },
                "meeting_user/14": {
                    "meeting_id": 1,
                    "user_id": 4,
                    "group_ids": [4],
                },
            },
        )
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request_multi(
                "user.send_invitation_email",
                [
                    {"id": 3, "meeting_id": 1},
                    {"id": 3, "meeting_id": 4},
                ],
            )
        self.assert_status_code(response, 200)
        self.assertEqual(len(handler.emails), 1)
        self.assertEqual(response.json["results"][0][0]["sent"], False)
        self.assertEqual(response.json["results"][0][0]["recipient_user_id"], 3)
        self.assertEqual(response.json["results"][0][0]["recipient_meeting_id"], 1)
        self.assertEqual(
            response.json["results"][0][0]["type"], EmailErrorType.SETTINGS_ERROR
        )
        self.assertIn(
            "Invalid characters in the sender name configuration of meeting 'annual general meeting', forbidden characters: '[', ']', '\\'.",
            response.json["results"][0][0]["message"],
        )

        self.assertEqual(response.json["results"][0][1]["sent"], True)
        self.assertEqual(response.json["results"][0][1]["recipient_user_id"], 3)
        self.assertEqual(response.json["results"][0][1]["recipient_meeting_id"], 4)

    # Tests regarding reply_to
    def test_reply_to_correct(self) -> None:
        self.set_models(
            {"meeting/1": {"users_email_replyto": "reply@example.com"}},
        )
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                    "meeting_id": 1,
                },
            )
        self.assert_status_code(response, 200)
        self.assertEqual(response.json["results"][0][0]["sent"], True)
        self.assertIn("Reply-To: reply@example.com", handler.emails[0]["data"])

    def test_reply_to_error(self) -> None:
        self.set_models(
            {"meeting/1": {"users_email_replyto": "reply@example"}},
        )
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                    "meeting_id": 1,
                },
            )
        self.assert_status_code(response, 200)
        self.assertEqual(response.json["results"][0][0]["sent"], False)
        self.assertEqual(
            response.json["results"][0][0]["type"], EmailErrorType.SETTINGS_ERROR
        )
        self.assertIn(
            "The given reply_to address 'reply@example' is not valid.",
            response.json["results"][0][0]["message"],
        )

    # permission test
    def test_permission_error(self) -> None:
        """allowed for meeting/1, forbidden for meeting 4"""
        self.create_meeting(4)
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": None,
                    "meeting_user_ids": [11, 12],
                    "meeting_ids": [1, 4],
                },
                "user/2": {
                    "meeting_user_ids": [13],
                    "meeting_ids": [1, 4],
                },
                "meeting_user/11": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
                "meeting_user/12": {
                    "meeting_id": 4,
                    "user_id": 1,
                    "group_ids": [4],
                },
                "meeting_user/13": {
                    "meeting_id": 4,
                    "user_id": 2,
                    "group_ids": [4],
                },
            },
        )
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request_multi(
                "user.send_invitation_email",
                [
                    {"id": 2, "meeting_id": 1},
                    {"id": 2, "meeting_id": 4},
                ],
            )
        self.assert_status_code(response, 200)
        self.assertEqual(len(handler.emails), 1)
        self.assertEqual(response.json["results"][0][0]["sent"], True)
        self.assertEqual(response.json["results"][0][0]["recipient_user_id"], 2)
        self.assertEqual(response.json["results"][0][0]["recipient_meeting_id"], 1)

        self.assertEqual(response.json["results"][0][1]["sent"], False)
        self.assertEqual(response.json["results"][0][1]["recipient_user_id"], 2)
        self.assertEqual(response.json["results"][0][1]["recipient_meeting_id"], 4)
        self.assertEqual(
            response.json["results"][0][1]["type"], EmailErrorType.USER_ERROR
        )
        self.assertIn(
            "Missing Permission: user.can_update",
            response.json["results"][0][1]["message"],
        )

    # formatting body and subject test
    def test_correct_subject_and_body_from_default(self) -> None:
        response = self.request(
            "meeting.create",
            {
                "committee_id": 60,
                "name": "Test Meeting",
                "language": "en",
                "admin_ids": [1],
            },
        )
        meeting_id = response.json["results"][0][0]["id"]
        self.set_models(
            {
                "user/2": {
                    "title": "Dr.",
                    "meeting_user_ids": [12],
                    "meeting_ids": [meeting_id],
                },
                "meeting_user/12": {
                    "meeting_id": meeting_id,
                    "user_id": 2,
                    "group_ids": [4],
                },
            }
        )
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                    "meeting_id": meeting_id,
                },
            )
        self.assert_status_code(response, 200)
        self.assertEqual(response.json["results"][0][0]["sent"], True)
        self.assertIn(
            'Content-Type: text/plain; charset="utf-8"',
            handler.emails[0]["data"],
        )
        self.assertNotIn(
            'Content-Type: text/html; charset="utf-8"',
            handler.emails[0]["data"],
        )
        self.assertIn(
            "Subject: OpenSlides access data",
            handler.emails[0]["data"],
        )
        self.assertIn(
            "Username: Testuser 2",
            handler.emails[0]["data"],
        )
        self.assertIn(
            "Dear Dr. Jim Beam",
            handler.emails[0]["data"],
        )
        self.assertIn(
            "Password: secret",
            handler.emails[0]["data"],
        )
        self.assertIn(
            "https://example.com",
            handler.emails[0]["data"],
        )

    def test_correct_modified_body(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_email_subject": "Invitation for Openslides '{event_name}'",
                    "users_email_body": "event name: {event_name}",
                }
            }
        )
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                    "meeting_id": 1,
                },
            )
        self.assert_status_code(response, 200)
        self.assertEqual(response.json["results"][0][0]["sent"], True)
        self.assertIn(
            "Subject: Invitation for Openslides 'annual general meeting'",
            handler.emails[0]["data"],
        )
        self.assertIn(
            "event name: annual general meeting",
            handler.emails[0]["data"],
        )

    def test_modified_body_with_unknown_keyword(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_email_subject": "Invitation for Openslides '{xevent_name}'",
                    "users_email_body": "event name: {yevent_name}",
                }
            }
        )
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                    "meeting_id": 1,
                },
            )
        self.assert_status_code(response, 200)
        self.assertEqual(response.json["results"][0][0]["sent"], True)
        self.assertIn(
            "Subject: Invitation for Openslides ''xevent_name''",
            handler.emails[0]["data"],
        )
        self.assertIn(
            "event name: 'yevent_name'",
            handler.emails[0]["data"],
        )

    def test_correct_organization_send(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "name": "test orga name",
                    "users_email_subject": "Invitation for Openslides '{event_name}'",
                    "users_email_body": "event name: {event_name}",
                },
            }
        )
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                },
            )
        self.assert_status_code(response, 200)
        print(response.json["results"])
        self.assertEqual(response.json["results"][0][0]["sent"], True)
        self.assertIn(
            "Subject: Invitation for Openslides 'test orga name'",
            handler.emails[0]["data"],
        )
        self.assertIn(
            "event name: test orga name",
            handler.emails[0]["data"],
        )

    def test_organization_send_no_permission(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": None},
                "user/2": {"username": "testx"},
                ONE_ORGANIZATION_FQID: {
                    "name": "test orga name",
                    "users_email_subject": "Invitation for Openslides '{event_name}'",
                    "users_email_body": "event name: {event_name}",
                },
            }
        )
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                },
            )
        self.assert_status_code(response, 200)
        self.assertEqual(response.json["results"][0][0]["sent"], False)
        self.assertEqual(
            response.json["results"][0][0]["type"], EmailErrorType.USER_ERROR
        )
        self.assertEqual(
            response.json["results"][0][0]["message"],
            "Missing OrganizationManagementLevel: can_manage_users Mail 1 from 1",
        )

    def test_with_parent_meeting_permission(self) -> None:
        self.assert_with_meeting_permission(Permissions.User.CAN_MANAGE)

    def test_with_meeting_permission(self) -> None:
        self.assert_with_meeting_permission(Permissions.User.CAN_UPDATE)

    def assert_with_meeting_permission(self, perm: Permission) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_email_subject": "Invitation for Openslides '{event_name}'",
                    "users_email_body": "event name: {event_name}",
                }
            }
        )
        self.set_group_permissions(3, [perm])
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                    "meeting_id": 1,
                },
            )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["sent"]

    def test_with_locked_meeting(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_email_subject": "Invitation for Openslides '{event_name}'",
                    "users_email_body": "event name: {event_name}",
                    "locked_from_inside": True,
                }
            }
        )
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                    "meeting_id": 1,
                },
            )
        self.assert_status_code(response, 200)
        assert not response.json["results"][0][0]["sent"]
        self.assertIn(
            "Missing Permission: user.can_update Mail 1 from 1",
            response.json["results"][0][0]["message"],
        )

    def test_correct_modified_body_new_placeholders(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "title": "Mr.",
                },
                "meeting_user/2": {
                    "structure_level_ids": [1, 2, 3],
                },
                "meeting/1": {
                    "users_email_subject": "Instructions for {title} {last_name} of group(s) {groups}",
                    "users_email_body": """Hello {first_name}!
Your shopping list: {structure_levels}.
Please ensure all of it is bought and brought over at least a week before new year's eve.""",
                    "structure_level_ids": [1, 2, 3],
                },
                "structure_level/1": {"name": "Rock sugar", "meeting_user_ids": [2]},
                "structure_level/2": {"name": "Anise", "meeting_user_ids": [2]},
                "structure_level/3": {"name": "Cardamom", "meeting_user_ids": [2]},
            }
        )
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                    "meeting_id": 1,
                },
            )
        self.assert_status_code(response, 200)
        self.assertEqual(response.json["results"][0][0]["sent"], True)
        self.assertIn(
            "Subject: Instructions for Mr. Beam of group(s) group1",
            handler.emails[0]["data"],
        )
        self.assertIn(
            "Hello Jim!\r\nYour shopping list: Rock sugar, Anise, Cardamom.\r\nPlease ensure all of it is bought and brought over at least a week before new=\r\n year's eve.",
            handler.emails[0]["data"],
        )

    def test_correct_organization_new_placeholders(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "title": "Mr.",
                },
                ONE_ORGANIZATION_FQID: {
                    "name": "test orga name",
                    "users_email_subject": "Instructions for {title} {last_name} of group(s) {groups}",
                    "users_email_body": """Hello {first_name}!
Your shopping list: {structure_levels}.
Please ensure all of it is bought and brought over at least a week before new year's eve.""",
                },
            }
        )
        handler = AIOHandler()
        with AiosmtpdServerManager(handler):
            response = self.request(
                "user.send_invitation_email",
                {
                    "id": 2,
                },
            )
        self.assert_status_code(response, 200)
        print(response.json["results"])
        self.assertEqual(response.json["results"][0][0]["sent"], True)
        self.assertIn(
            "Subject: Instructions for Mr. Beam of group(s) 'groups'",
            handler.emails[0]["data"],
        )
        self.assertIn(
            "Hello Jim!\r\nYour shopping list: 'structure_levels'.\r\nPlease ensure all of it is bought and brought over at least a week before new=\r\n year's eve.",
            handler.emails[0]["data"],
        )
