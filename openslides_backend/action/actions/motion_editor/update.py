from ....models.models import MotionEditor
from ...mixins.motion_meeting_user_update import build_motion_meeting_user_update_action
from ...util.action_type import ActionType
from ...util.register import register_action

BaseClass: type = build_motion_meeting_user_update_action(MotionEditor)


@register_action("motion_editor.update", action_type=ActionType.BACKEND_INTERNAL)
class MotionEditorUpdateAction(BaseClass):
    """
    Action to update a motion_editor's weight. Should only be called by user.merge.
    """
