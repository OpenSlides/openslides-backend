from ....models.models import MotionSubmitter
from ...mixins.motion_meeting_user_delete import build_motion_meeting_user_delete_action
from ...util.register import register_action

BaseClass: type = build_motion_meeting_user_delete_action(MotionSubmitter)


@register_action("motion_submitter.delete")
class MotionSubmitterDeleteAction(BaseClass):
    history_information = "Submitters changed"
    history_relation_field = "motion_id"
