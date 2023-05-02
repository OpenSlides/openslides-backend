from typing import Any, Dict

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.schema import optional_id_schema
from ....shared.util import ONE_ORGANIZATION_ID
from ...generics.create import CreateAction
from ...mixins.send_email_mixin import EmailCheckMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create_update_permissions_mixin import CreateUpdatePermissionsMixin
from .password_mixin import PasswordCreateMixin
from .user_mixin import LimitOfUserMixin, UserMixin, UsernameMixin


@register_action("user.create")
class UserCreate(
    EmailCheckMixin,
    CreateAction,
    UserMixin,
    CreateUpdatePermissionsMixin,
    PasswordCreateMixin,
    LimitOfUserMixin,
    UsernameMixin,
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
            "default_number",
            "default_structure_level",
            "default_vote_weight",
            "organization_management_level",
            "is_present_in_meeting_ids",
            "committee_management_ids",
            "is_demo_user",
            "forwarding_committee_ids",
        ],
        additional_optional_fields={
            "meeting_id": optional_id_schema,
            **UserMixin.transfer_field_list,
        },
    )
    check_email_field = "email"
    history_information = "Account created"
    own_history_information_first = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        if instance.get("is_active"):
            self.check_limit_of_user(1)
        if not (
            instance.get("username")
            or instance.get("first_name")
            or instance.get("last_name")
        ):
            raise ActionException("Need username or first_name or last_name")

        if not instance.get("username"):
            instance["username"] = self.generate_username(instance)
        if not instance.get("default_password"):
            instance = self.generate_and_set_password(instance)
        else:
            instance = self.set_password(instance)
        instance["organization_id"] = ONE_ORGANIZATION_ID
        return instance
