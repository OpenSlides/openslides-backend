from ....models.models import MotionSubmitter
from ...mixins.motion_meeting_user_create import build_motion_meeting_user_create_action
from ...util.register import register_action

BaseClass: type = build_motion_meeting_user_create_action(MotionSubmitter)


@register_action("motion_submitter.create")
class MotionSubmitterCreateAction(BaseClass):
    history_information = "Submitters changed"
    history_relation_field = "motion_id"
