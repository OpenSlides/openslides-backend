from collections import defaultdict
from email.headerregistry import Address
from enum import Enum
from smtplib import (
    SMTPAuthenticationError,
    SMTPDataError,
    SMTPRecipientsRefused,
    SMTPSenderRefused,
    SMTPServerDisconnected,
)
from ssl import SSLCertVerificationError
from time import time
from typing import Any

from fastjsonschema import JsonSchemaException

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import (
    has_organization_management_level,
    has_perm,
)
from ....permissions.permissions import Permissions
from ....shared.exceptions import DatastoreException, MissingPermission
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import optional_id_schema
from ....shared.util import ONE_ORGANIZATION_ID
from ...generics.update import UpdateAction
from ...mixins.send_email_mixin import EmailSettings, EmailUtils
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResults


class EmailErrorType(str, Enum):
    USER_ERROR = "user_error"
    SETTINGS_ERROR = "settings_error"
    CONFIGURATION_ERROR = "configuration_error"
    OTHER_ERROR = "other_error"


@register_action("user.send_invitation_email")
class UserSendInvitationMail(UpdateAction):
    """
    Action send an invitation mail to a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        additional_optional_fields={"meeting_id": optional_id_schema},
    )

    def perform(
        self, action_data: ActionData, user_id: int, internal: bool = False
    ) -> tuple[WriteRequest | None, ActionResults | None]:
        self.user_id = user_id
        self.index = 0
        global_result: dict[str, Any] = {"sent": False}

        if not EmailUtils.check_email(EmailSettings.default_from_email):
            global_result["message"] = (
                f"email {EmailSettings.default_from_email} is not a valid sender email address."
            )
            global_result["type"] = EmailErrorType.CONFIGURATION_ERROR
            self.results.append(global_result)
            return (None, self.results)

        try:
            with EmailUtils.get_mail_connection() as mail_client:
                self.index = -1
                self.mail_client = mail_client
                for instance in action_data:
                    self.index += 1
                    result = self.get_initial_result_false(instance)
                    try:
                        self.validate_instance(instance)
                        if instance.get("meeting_id"):
                            self.check_for_archived_meeting(instance)
                        self.check_permissions(instance)
                        instance = self.update_instance(instance)
                        result = instance.pop("result")
                    except SMTPRecipientsRefused as e:
                        result["message"] = f"SMTPRecipientsRefused: {str(e)}"
                        result["type"] = EmailErrorType.CONFIGURATION_ERROR
                    except SMTPServerDisconnected as e:
                        result["message"] = (
                            f"SMTPServerDisconnected: {str(e)} during transmission"
                        )
                        result["type"] = EmailErrorType.CONFIGURATION_ERROR
                    except JsonSchemaException as e:
                        result["message"] = f"JsonSchema: {str(e)}"
                        result["type"] = EmailErrorType.OTHER_ERROR
                    except DatastoreException as e:
                        result["message"] = f"DatastoreException: {str(e)}"
                        result["type"] = EmailErrorType.OTHER_ERROR
                    except MissingPermission as e:
                        result["message"] = e.message
                        result["type"] = EmailErrorType.USER_ERROR
                    except SMTPDataError as e:
                        result["message"] = f"SMTPDataError: {str(e)}"
                        result["type"] = EmailErrorType.CONFIGURATION_ERROR
                    except SMTPSenderRefused as e:
                        raise e
                    except Exception as e:
                        result["message"] = f"Exception: {str(e)}"

                    if result["sent"]:
                        instance.pop("meeting_id", None)
                        events = self.create_events(instance)
                        self.events.extend(events)
                    else:
                        result["message"] = (
                            str(result["message"])
                            + f" Mail {self.index+1} from {len(list(action_data))}"
                        )

                    self.results.append(result)
            global_result = {}
        except SMTPAuthenticationError as e:
            global_result["message"] = f"SMTPAuthenticationError: {str(e)}"
            global_result["type"] = EmailErrorType.CONFIGURATION_ERROR
        except SMTPSenderRefused as e:
            global_result["message"] = f"SMTPSenderRefused: {str(e)}"
            global_result["type"] = EmailErrorType.CONFIGURATION_ERROR
        except ConnectionRefusedError as e:
            global_result["message"] = f"ConnectionRefusedError: {str(e)}"
            global_result["type"] = EmailErrorType.CONFIGURATION_ERROR
        except SSLCertVerificationError as e:
            global_result["message"] = f"SSLCertVerificationError: {str(e)}"
            global_result["type"] = EmailErrorType.CONFIGURATION_ERROR
        except Exception as e:
            global_result["message"] = (
                f"Unspecified mail connection exception on sending invitation email to server {EmailSettings.host}, port {EmailSettings.port}: {str(e)}"
            )
            global_result["type"] = EmailErrorType.CONFIGURATION_ERROR

        if global_result:
            self.results.append(global_result)

        write_request = self.build_write_request()
        return (write_request, self.results)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        user_id = instance["id"]
        meeting_id = instance.get("meeting_id")

        result = self.get_initial_result_false(instance)
        instance["result"] = result

        user = self.datastore.get(
            fqid_from_collection_and_id("user", user_id),
            [
                "meeting_ids",
                "email",
                "username",
                "last_name",
                "first_name",
                "title",
                "default_password",
            ],
        )
        if not (to_email := user.get("email")):
            result["message"] = f"'{user['username']}' has no email address."
            result["type"] = EmailErrorType.USER_ERROR
            return instance
        if not EmailUtils.check_email(to_email):
            result["message"] = f"'{user['username']}' has no valid email address."
            result["type"] = EmailErrorType.USER_ERROR
            return instance
        result["recipient"] = to_email

        if meeting_id and meeting_id not in user["meeting_ids"]:
            result["message"] = (
                f"'{user['username']}' does not belong to meeting/{meeting_id}."
            )
            result["type"] = EmailErrorType.USER_ERROR
            return instance

        mail_data = self.get_data_from_meeting_or_organization(meeting_id)
        if users_email_sender := mail_data.get("users_email_sender", "").strip():
            if any(
                x in users_email_sender for x in EmailUtils.SENDER_NAME_FORBIDDEN_CHARS
            ):
                result["message"] = (
                    f"Invalid characters in the sender name configuration of meeting '{mail_data['name']}', forbidden characters: '"
                    + "', '".join(EmailUtils.SENDER_NAME_FORBIDDEN_CHARS)
                    + "'."
                )
                result["type"] = EmailErrorType.SETTINGS_ERROR
                return instance
            from_email = str(
                Address(users_email_sender, addr_spec=EmailSettings.default_from_email)
            )
        else:
            from_email = EmailSettings.default_from_email

        if (
            reply_to := mail_data.get("users_email_replyto", "")
        ) and not EmailUtils.check_email(reply_to):
            result["message"] = f"The given reply_to address '{reply_to}' is not valid."
            result["type"] = EmailErrorType.SETTINGS_ERROR
            return instance

        class format_dict(defaultdict):
            def __missing__(self, key: str) -> str:
                return f"'{key}'"

        subject_format = format_dict(
            None,
            {
                "event_name": mail_data.get("name", ""),
                "name": self.get_verbose_username(user),
                "username": user.get("username", ""),
            },
        )
        body_dict = {
            "password": user.get("default_password", ""),
            "url": mail_data.get("url", ""),
            **subject_format,
        }

        body_format = format_dict(None, body_dict)

        EmailUtils.send_email(
            self.mail_client,
            from_email,
            to_email,
            mail_data.get("users_email_subject", "").format_map(subject_format),
            mail_data.get("users_email_body", "").format_map(body_format),
            reply_to=reply_to,
            html=False,
        )
        result["sent"] = True
        instance["last_email_sent"] = round(time())
        return super().update_instance(instance)

    def get_data_from_meeting_or_organization(
        self, meeting_id: int | None
    ) -> dict[str, Any]:
        fields = [
            "name",
            "users_email_sender",
            "users_email_replyto",
            "users_email_subject",
            "users_email_body",
        ]
        if not meeting_id:
            collection = "organization"
            id_ = ONE_ORGANIZATION_ID
            fields.append("url")
        else:
            collection = "meeting"
            id_ = meeting_id

        res = self.datastore.get(
            fqid_from_collection_and_id(collection, id_),
            fields,
            lock_result=False,
        )
        if meeting_id:
            organization = self.datastore.get(
                ONE_ORGANIZATION_FQID,
                ["url"],
                lock_result=False,
            )
            res["url"] = organization.get("url", "")
        return res

    def get_verbose_username(self, instance: dict[str, Any]) -> str:
        first_name = instance.get("first_name", "").strip()
        last_name = instance.get("last_name", "").strip()

        if first_name and last_name:
            name = " ".join((first_name, last_name))
        else:
            name = first_name or last_name or instance.get("username", "")

        if title := instance.get("title", "").strip():
            name = " ".join([title, name])
        return name

    def validate_instance(self, instance: dict[str, Any]) -> None:
        type(self).schema_validator(instance)

    def get_initial_result_false(self, instance: dict[str, Any]) -> dict[str, Any]:
        return {
            "sent": False,
            "recipient_user_id": instance.get("id"),
            "recipient_meeting_id": instance.get("meeting_id"),
        }

    def check_permissions(self, instance: dict[str, Any]) -> None:
        if instance.get("meeting_id") and has_perm(
            self.datastore,
            self.user_id,
            Permissions.User.CAN_MANAGE,
            instance["meeting_id"],
        ):
            return
        if has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            return
        if instance.get("meeting_id"):
            raise MissingPermission(Permissions.User.CAN_MANAGE)
        else:
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_USERS)
