from tests.system.action.base_motion_meeting_user_delete_test import (
    build_motion_meeting_user_delete_test,
)

BaseClass: type = build_motion_meeting_user_delete_test("motion_editor")


class MotionEditorDeleteTest(BaseClass):
    __test__ = True
