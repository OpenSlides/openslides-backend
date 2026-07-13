from ....models.models import MeetingPollDefault
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_poll_default.update", action_type=ActionType.BACKEND_INTERNAL)
class MeetingPollDefaultUpdate(UpdateAction):
    """
    Action to update a meeting_poll_default.
    """

    model = MeetingPollDefault()
    schema = DefaultSchema(MeetingPollDefault()).get_update_schema(
        optional_properties=[
            "allow_abstain",
            "allow_nota",
            "display_chart",
            "group_ids",
            "onehundred_percent_base",
            "sort_result_by_votes",
            "strike_out",
            "visibility",
        ]
    )
