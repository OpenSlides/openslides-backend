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
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import (
    has_organization_management_level,
    has_perm,
)
from ....permissions.permissions import Permissions
from ....shared.exceptions import DatastoreException, MissingPermission
from ....shared.interfaces.write_request import WriteRequest
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import optional_id_schema
from ...generics.update import UpdateAction
from ...mixins.send_email_mixin import EmailMixin, EmailSettings
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResults
from .helper import get_user_name

ONE_ORGANIZATION = 1


@register_action("user.send_invitation_email")
class UserSendInvitationMail(EmailMixin, UpdateAction):
    """
    Action send an invitation mail to a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        additional_optional_fields={"meeting_id": optional_id_schema},
    )

    def perform(
        self, action_data: ActionData, user_id: int, internal: bool = False
    ) -> Tuple[Optional[WriteRequest], Optional[ActionResults]]:
        self.user_id = user_id
        self.index = 0
        if not EmailMixin.check_email(EmailSettings.default_from_email):
            result = {
                "sent": False,
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
                        if instance.get("meeting_id"):
                            self.check_for_archived_meeting(instance)
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

                    if result["sent"]:
                        write_request = self.create_write_requests(instance)
                        self.write_requests.extend(write_request)

                    self.results.append(result)
        except SMTPAuthenticationError as e:
            result = {"sent": False, "message": f"SMTPAuthenticationError: {str(e)}"}
            self.results.append(result)
        except SMTPSenderRefused as e:
            result = {
                "sent": False,
                "message": f"SMTPSenderRefused: {str(e)}",
            }
            self.results.append(result)
        except ConnectionRefusedError as e:
            result = {"sent": False, "message": f"ConnectionRefusedError: {str(e)}"}
            self.results.append(result)
        except SSLCertVerificationError as e:
            result = {"sent": False, "message": f"SSLCertVerificationError: {str(e)}"}
            self.results.append(result)
        except Exception as e:
            result = {
                "sent": False,
                "message": f"Unspecified mail connection exception on sending invitation email to server {EmailSettings.host}, port {EmailSettings.port}: {str(e)}",
            }
            self.results.append(result)

        final_write_request = self.process_write_requests()
        return (final_write_request, self.results)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        user_id = instance["id"]
        meeting_id = instance.get("meeting_id")

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

        if meeting_id and meeting_id not in user["meeting_ids"]:
            result[
                "message"
            ] = f"User/{user_id} does not belong to meeting/{meeting_id}"
            return instance

        mail_data = self.get_data_from_meeting_or_organization(meeting_id)
        from_email: Union[str, Address]
        if users_email_sender := mail_data.get("users_email_sender", "").strip():
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
            reply_to := mail_data.get("users_email_replyto", "")
        ) and not self.check_email(reply_to):
            result["message"] = f"The given reply_to address '{reply_to}' is not valid."
            return instance

        class format_dict(defaultdict):
            def __missing__(self, key: str) -> str:
                return f"'{key}'"

        subject_format = format_dict(
            None,
            {
                "event_name": mail_data.get("name", ""),
                "name": get_user_name(user),
                "username": user.get("username", ""),
            },
        )
        body_dict = {
            "password": user.get("default_password", ""),
            "url": mail_data.get("url", ""),
            **subject_format,
        }

        body_format = format_dict(None, body_dict)

        self.send_email(
            self.mail_client,
            from_email,
            to_email,
            mail_data.get("users_email_subject", "").format_map(subject_format),
            mail_data.get("users_email_body", "").format_map(body_format),
            reply_to=reply_to,
            html=False,
        )
        result["sent"] = True
        instance["last_email_send"] = round(time())
        return super().update_instance(instance)

    def get_data_from_meeting_or_organization(
        self, meeting_id: Optional[int]
    ) -> Dict[str, Any]:
        fields = [
            "name",
            "users_email_sender",
            "users_email_replyto",
            "users_email_subject",
            "users_email_body",
        ]
        if not meeting_id:
            collection = Collection("organization")
            id_ = ONE_ORGANIZATION
            fields.append("url")
        else:
            collection = Collection("meeting")
            id_ = meeting_id

        res = self.datastore.fetch_model(
            FullQualifiedId(collection, id_),
            fields,
            lock_result=False,
        )
        if meeting_id:
            organization = self.datastore.fetch_model(
                FullQualifiedId(Collection("organization"), ONE_ORGANIZATION),
                ["url"],
                lock_result=False,
            )
            res["url"] = organization.get("url", "")
        return res

    def validate_instance(self, instance: Dict[str, Any]) -> None:
        type(self).schema_validator(instance)

    def get_initial_result_false(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "sent": False,
            "recipient_user_id": instance.get("id"),
            "recipient_meeting_id": instance.get("meeting_id"),
        }

    def check_permissions(self, instance: Dict[str, Any]) -> None:
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
