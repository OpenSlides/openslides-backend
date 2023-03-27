from typing import Any, Dict

from openslides_backend.shared.exceptions import ActionException

from ....models.models import MeetingUser
from ....permissions.permissions import Permissions
from ....shared.filters import And, FilterOperator
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixin import MeetingUserMixin


@register_action("meeting_user.create")
class MeetingUserCreate(MeetingUserMixin, CreateAction):
    """
    Action to create a meeting user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_create_schema(
        required_properties=["user_id", "meeting_id"],
        optional_properties=[
            "about_me",
            "group_ids",
            *MeetingUserMixin.standard_fields,
        ],
    )
    permission = Permissions.User.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        filter_ = And(
            FilterOperator("meeting_id", "=", instance["meeting_id"]),
            FilterOperator("user_id", "=", instance["user_id"]),
        )
        if self.datastore.exists("meeting_user", filter_):
            raise ActionException(
                f"MeetingUser instance with user {instance['user_id']} and meeting {instance['meeting_id']} already exists"
            )
        return super().update_instance(instance)
