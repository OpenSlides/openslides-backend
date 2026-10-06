from ....models.models import MeetingPollSetting
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_poll_setting.update", action_type=ActionType.BACKEND_INTERNAL)
class MeetingPollSettingUpdate(UpdateAction):
    """
    Action to update a meeting_poll_setting.
    """

    model = MeetingPollSetting()
    schema = DefaultSchema(MeetingPollSetting()).get_update_schema(
        optional_properties=[
            "allow_live_voting",
            "group_ids",
            "enable_cumulative_voting",
            "enable_live_voting",
            "enable_max_options_limit",
            "enable_max_yes_votes",
            "method",
            "onehundred_percent_base",
            "required_majority",
            "sort_result_by_votes",
            "visibility",
        ],
    )
