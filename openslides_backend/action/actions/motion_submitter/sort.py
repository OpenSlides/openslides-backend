from ....models.models import MotionSubmitter
from ...mixins.motion_meeting_user_sort import build_motion_meeting_user_sort_action
from ...util.register import register_action

BaseClass: type = build_motion_meeting_user_sort_action(
    MotionSubmitter, "motion_submitter_ids"
)


@register_action("motion_submitter.sort")
class MotionSubmitterSort(BaseClass):
    pass
