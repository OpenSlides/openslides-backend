from ....models.models import MeetingPollSetting
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_poll_setting.delete", action_type=ActionType.BACKEND_INTERNAL)
class MeetingPollSettingDelete(DeleteAction):
    """
    Action to delete a meeting_poll_setting.
    """

    model = MeetingPollSetting()
    schema = DefaultSchema(MeetingPollSetting()).get_delete_schema()
