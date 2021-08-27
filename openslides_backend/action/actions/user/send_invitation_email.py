from collections import defaultdict
from email.headerregistry import Address
from smtplib import (
    SMTPAuthenticationError,
    SMTPDataError,
    SMTPRecipientsRefused,
    SMTPSenderRefused,
    SMTPServerDisconnected,
)
from ssl import SSLCertVerificationError
from time import time
from typing import Any, Dict, Optional, Tuple, Union

from fastjsonschema import JsonSchemaException

from ....models.models import User
from ....permissions.permissions import Permissions
from ....shared.exceptions import DatastoreException, MissingPermission
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...mixins.send_email_mixin import EmailMixin, EmailSettings
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResults
from .helper import get_user_name


@register_action("user.send_invitation_email")
class UserSendInvitationMail(EmailMixin, UpdateAction):
    """
    Action send an invitation mail to a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        required_properties=["id"],
        additional_required_fields={"meeting_id": required_id_schema},
    )
    permission = Permissions.User.CAN_MANAGE

    def perform(
        self, action_data: ActionData, user_id: int, internal: bool = False
    ) -> Tuple[Optional[WriteRequest], Optional[ActionResults]]:
        self.user_id = user_id
        self.index = 0
        if not EmailMixin.check_email(EmailSettings.default_from_email):
            result = {
                "send": False,
                "message": f"email {EmailSettings.default_from_email} is not a valid sender email address.",
            }
            self.results.append(result)
            return (None, self.results)

        try:
            with EmailMixin.get_mail_connection() as mail_client:
                self.index = -1
                self.mail_client = mail_client
                for instance in action_data:
                    self.index += 1
                    result = self.get_initial_result_false(instance)
                    try:
                        self.validate_instance(instance)
                        self.check_permissions(instance)
                        instance = self.update_instance(instance)
                        result = instance.pop("result")
                    except SMTPRecipientsRefused as e:
                        result["message"] = f"SMTPRecipientsRefused: {str(e)}"
                    except SMTPServerDisconnected as e:
                        result[
                            "message"
                        ] = f"SMTPServerDisconnected: {str(e)} during transmission"
                    except JsonSchemaException as e:
                        result["message"] = f"JsonSchema: {str(e)}"
                    except DatastoreException as e:
                        result["message"] = f"DatastoreException: {str(e)}"
                    except MissingPermission as e:
                        result["message"] = e.message
                    except SMTPDataError as e:
                        result["message"] = f"SMTPDataError: {str(e)}"

                    if result["send"]:
                        write_request = self.create_write_requests(instance)
                        self.write_requests.extend(write_request)

                    self.results.append(result)
        except SMTPAuthenticationError as e:
            result = {"send": False, "message": f"SMTPAuthenticationError: {str(e)}"}
            self.results.append(result)
        except SMTPSenderRefused as e:
            result = {
                "send": False,
                "message": f"SMTPSenderRefused: {str(e)}",
            }
            self.results.append(result)
        except ConnectionRefusedError as e:
            result = {"send": False, "message": f"ConnectionRefusedError: {str(e)}"}
            self.results.append(result)
        except SSLCertVerificationError as e:
            result = {"send": False, "message": f"SSLCertVerificationError: {str(e)}"}
            self.results.append(result)

        final_write_request = self.process_write_requests()
        return (final_write_request, self.results)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        user_id = instance["id"]
        meeting_id = instance["meeting_id"]

        result = self.get_initial_result_false(instance)
        instance["result"] = result

        user = self.datastore.get(
            FullQualifiedId(Collection("user"), user_id),
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
            result["message"] = f"User/{user_id} has no email-address."
            return instance
        if not self.check_email(to_email):
            result[
                "message"
            ] = f"The email-address {to_email} of User/{user_id} is not valid."
            return instance
        result["recipient"] = to_email

        if meeting_id not in user["meeting_ids"]:
            result[
                "message"
            ] = f"User/{user_id} does not belong to meeting/{meeting_id}"
            return instance

        meeting = self.datastore.fetch_model(
            FullQualifiedId(Collection("meeting"), meeting_id),
            [
                "name",
                "users_email_sender",
                "users_email_replyto",
                "users_email_subject",
                "users_email_body",
                "users_pdf_url",
            ],
            lock_result=False,
        )

        from_email: Union[str, Address]
        if users_email_sender := meeting.get("users_email_sender", "").strip():
            blacklist = ("[", "]", "\\")
            if any(x in users_email_sender for x in blacklist):
                result["message"] = (
                    f'Invalid characters in the sender name configuration of meeting_id "{meeting_id}". Not allowed chars: "'
                    + '", "'.join(blacklist)
                    + '"'
                )
                return instance
            from_email = Address(
                users_email_sender, addr_spec=EmailSettings.default_from_email
            )
        else:
            from_email = EmailSettings.default_from_email

        if (
            reply_to := meeting.get("users_email_replyto", "")
        ) and not self.check_email(reply_to):
            result["message"] = f"The given reply_to address '{reply_to}' is not valid."
            return instance

        class format_dict(defaultdict):
            def __missing__(self, key: str) -> str:
                return f"'{key}'"

        subject_format = format_dict(
            None,
            {
                "event_name": meeting.get("name", ""),
                "name": get_user_name(user),
                "username": user.get("username", ""),
            },
        )
        body_format = format_dict(
            None,
            {
                "url": meeting.get("users_pdf_url", ""),
                "password": user.get("default_password", ""),
                **subject_format,
            },
        )

        result["send"] = True
        self.send_email(
            self.mail_client,
            from_email,
            to_email,
            meeting.get("users_email_subject", "").format_map(subject_format),
            meeting.get("users_email_body", "").format_map(body_format),
            reply_to=reply_to,
            html=False,
        )
        instance["last_email_send"] = time()
        return super().update_instance(instance)

    def validate_instance(self, instance: Dict[str, Any]) -> None:
        type(self).schema_validator(instance)

    def get_initial_result_false(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "send": False,
            "recipient_user_id": instance.get("id"),
            "recipient_meeting_id": instance.get("meeting_id"),
        }
