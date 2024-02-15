from ....models.models import MotionEditor
from ...mixins.motion_meeting_user_sort import build_motion_meeting_user_sort_action
from ...util.register import register_action

BaseClass: type = build_motion_meeting_user_sort_action(
    MotionEditor, "motion_editor_ids"
)


@register_action("motion_editor.sort")
class MotionEditorSort(BaseClass):
    pass
