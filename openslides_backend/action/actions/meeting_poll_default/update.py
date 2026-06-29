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
            "ballot_paper_selection",
            "ballot_paper_number",
            "sort_result_by_votes",
            "visibility",
            "allow_abstain",
            "allow_nota",
            "strike_out",
            "onehundred_percent_base",
            "group_ids",
            "display_chart",
        ],
    )
