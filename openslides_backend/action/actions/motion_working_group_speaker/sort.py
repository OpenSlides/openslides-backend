from ....models.models import MotionWorkingGroupSpeaker
from ...mixins.motion_meeting_user_sort import build_motion_meeting_user_sort_action
from ...util.register import register_action

BaseClass: type = build_motion_meeting_user_sort_action(
    MotionWorkingGroupSpeaker, "motion_working_group_speaker_ids"
)


@register_action("motion_working_group_speaker.sort")
class MotionWorkingGroupSpeakerSort(BaseClass):
    pass
