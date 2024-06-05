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

    merge_fields = ["motion_submitter_ids", "assignment_candidate_ids"]

    model = MeetingUser()
    schema = DefaultSchema(MeetingUser()).get_update_schema(
        optional_properties=[
            "about_me",
            "group_ids",
            *meeting_user_standard_fields,
            *merge_fields,
        ],
        additional_optional_fields={"unsafe": {"type": "boolean"}},
    )
    extend_history_to = "user_id"

    def validate_fields(self, instance: dict[str, Any]) -> dict[str, Any]:
        if (not instance.pop("unsafe", False)) and len(
            forbidden := {field for field in self.merge_fields if field in instance}
        ):
            raise ActionException(
                f"data must not contain {forbidden} properties"
            )  # TODO: Test this
        return super().validate_fields(instance)
