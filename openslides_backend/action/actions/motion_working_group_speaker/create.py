from ....models.models import MotionWorkingGroupSpeaker
from ...mixins.motion_meeting_user_create import build_motion_meeting_user_create_action
from ...util.register import register_action

BaseClass: type = build_motion_meeting_user_create_action(MotionWorkingGroupSpeaker)


@register_action("motion_working_group_speaker.create")
class MotionWorkingGroupSpeakerCreateAction(BaseClass):
    pass
