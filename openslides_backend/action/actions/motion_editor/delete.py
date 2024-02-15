from ....models.models import MotionEditor
from ...mixins.motion_meeting_user_delete import build_motion_meeting_user_delete_action
from ...util.register import register_action

BaseClass: type = build_motion_meeting_user_delete_action(MotionEditor)


@register_action("motion_editor.delete")
class MotionEditorDeleteAction(BaseClass):
    pass
