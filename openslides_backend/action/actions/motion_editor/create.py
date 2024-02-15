from ....models.models import MotionEditor
from ...mixins.motion_meeting_user_create import build_motion_meeting_user_create_action
from ...util.register import register_action

BaseClass: type = build_motion_meeting_user_create_action(MotionEditor)


@register_action("motion_editor.create")
class MotionEditorCreateAction(BaseClass):
    pass
