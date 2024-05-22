from typing import Any

from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin

from ....models.models import MeetingUser
from ....shared.exceptions import ActionException
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .history_mixin import MeetingUserHistoryMixin
from .mixin import meeting_user_standard_fields


@register_action("meeting_user.update", action_type=ActionType.BACKEND_INTERNAL)
class MeetingUserUpdate(MeetingUserHistoryMixin, UpdateAction, ExtendHistoryMixin):
    """
    Action to update a meeting_user.
    """

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_update_schema(
        optional_properties=[
            "about_me",
            "group_ids",
            "user_id",
            *meeting_user_standard_fields,
        ],
    )
    extend_history_to = "user_id"

    def validate_fields(self, instance: dict[str, Any]) -> dict[str, Any]:
        if "user_id" in instance and not self.internal:
            raise ActionException("data must not contain {'user_id'} properties")
        return super().validate_fields(instance)
