from ....models.models import MotionSubmitter
from ...mixins.motion_meeting_user_update import build_motion_meeting_user_update_action
from ...util.action_type import ActionType
from ...util.register import register_action

BaseClass: type = build_motion_meeting_user_update_action(MotionSubmitter)


@register_action("motion_submitter.update", action_type=ActionType.BACKEND_INTERNAL)
class MotionSubmitterUpdateAction(BaseClass):
    """
    Action to update a motion_submitter's weight. Should only be called by user.merge.
    """
