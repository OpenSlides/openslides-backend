from ....models.models import MotionWorkingGroupSpeaker
from ...mixins.motion_meeting_user_update import build_motion_meeting_user_update_action
from ...util.action_type import ActionType
from ...util.register import register_action

BaseClass: type = build_motion_meeting_user_update_action(MotionWorkingGroupSpeaker)


@register_action(
    "motion_working_group_speaker.update", action_type=ActionType.BACKEND_INTERNAL
)
class MotionWorkingGroupSpeakerUpdateAction(BaseClass):
    """
    Action to update a motion_working_group_speaker's weight. Should only be called by user.merge.
    """
