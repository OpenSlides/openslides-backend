from ....models.models import MotionWorkingGroupSpeaker
from ...mixins.motion_meeting_user_delete import build_motion_meeting_user_delete_action
from ...util.register import register_action

BaseClass: type = build_motion_meeting_user_delete_action(MotionWorkingGroupSpeaker)


@register_action("motion_working_group_speaker.delete")
class MotionWorkingGroupSpeakerDeleteAction(BaseClass):
    pass
