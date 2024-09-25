import re
from typing import Any

from openslides_backend.permissions.permissions import Permissions

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.schema import optional_id_schema
from ....shared.util import ONE_ORGANIZATION_ID
from ...generics.create import CreateAction
from ...mixins.meeting_user_helper import get_meeting_user
from ...mixins.send_email_mixin import EmailCheckMixin
from ...util.crypto import get_random_password
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionResultElement
from ..meeting_user.mixin import CheckLockOutPermissionMixin
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .user_mixins import LimitOfUserMixin, UserMixin, UsernameMixin, check_gender_helper


@register_action("user.create")
class UserCreate(
    EmailCheckMixin,
    CreateAction,
    CreateUpdatePermissionsMixin,
    LimitOfUserMixin,
    UsernameMixin,
    CheckLockOutPermissionMixin,
):
    """
    Action to create a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_create_schema(
        optional_properties=[
            "title",
            "username",
            "pronoun",
            "first_name",
            "last_name",
            "is_active",
            "is_physical_person",
            "default_password",
            "can_change_own_password",
            "gender",
            "email",
            "default_vote_weight",
            "organization_management_level",
            "is_present_in_meeting_ids",
            "committee_management_ids",
            "is_demo_user",
            "forwarding_committee_ids",
            "saml_id",
            "member_number",
        ],
        additional_optional_fields={
            "meeting_id": optional_id_schema,
            **UserMixin.transfer_field_list,
        },
    )
    permission = Permissions.User.CAN_MANAGE
    check_email_field = "email"
    history_information = "Account created"
    own_history_information_first = True

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        self.meeting_id: int | None = instance.get("meeting_id")

        if instance.get("is_active"):
            self.check_limit_of_user(1)
        saml_id = instance.get("saml_id")
        if not instance.get("username"):
            if saml_id:
                instance["username"] = saml_id
            else:
                if not (instance.get("first_name") or instance.get("last_name")):
                    raise ActionException("Need username or first_name or last_name")
                instance["username"] = self.generate_username(instance)
        elif re.search(r"\s", instance["username"]):
            raise ActionException("Username may not contain spaces")
        self.check_locking_status(instance.get("meeting_id"), instance, None, None)
        instance = super().update_instance(instance)
        if saml_id:
            instance["can_change_own_password"] = False
            instance["password"] = None
            if instance.get("default_password"):
                raise ActionException(
                    f"user {instance['saml_id']} is a Single Sign On user and may not set the local default_passwort or the right to change it locally."
                )
        else:
            if not instance.get("default_password"):
                instance["default_password"] = get_random_password()
            self.reset_password(instance)
        instance["organization_id"] = ONE_ORGANIZATION_ID
        check_gender_helper(self.datastore, instance)
        return instance

    def create_action_result_element(
        self, instance: dict[str, Any]
    ) -> ActionResultElement | None:
        result = {"id": instance["id"]}
        if self.meeting_id:
            meeting_user = get_meeting_user(
                self.datastore, self.meeting_id, instance["id"], ["id"]
            )
            if meeting_user and meeting_user.get("id"):
                result["meeting_user_id"] = meeting_user["id"]
        return result
