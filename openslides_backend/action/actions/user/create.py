import re
from typing import Any, Dict, Optional

from openslides_backend.shared.patterns import fqid_from_collection_and_id
from openslides_backend.shared.typing import HistoryInformation

from ....models.models import User
from ....shared.exceptions import ActionException
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
            "committee_$_management_level",
            "group_$_ids",
            "vote_delegations_$_from_ids",
            "vote_delegated_$_to_id",
            "comment_$",
            "number_$",
            "structure_level_$",
            "about_me_$",
            "vote_weight_$",
            "is_demo_user",
            "forwarding_committee_ids",
        ],
    )
    check_email_field = "email"

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

    def generate_username(self, instance: Dict[str, Any]) -> str:
        return self.generate_usernames(
            [
                re.sub(
                    r"\W",
                    "",
                    instance.get("first_name", "") + instance.get("last_name", ""),
                )
            ]
        )[0]

    def get_history_information(self) -> Optional[HistoryInformation]:
        information = {}
        for instance in self.instances:
            meeting_ids = list(instance.get("group_$_ids", []))
            instance_information = ["Participant created"]
            if len(meeting_ids) == 1:
                instance_information[0] += " in meeting {}"
                instance_information.append(
                    fqid_from_collection_and_id("meeting", meeting_ids.pop())
                )
            information[
                fqid_from_collection_and_id(self.model.collection, instance["id"])
            ] = instance_information
        return information
