from tests.system.action.base_motion_meeting_user_create_test import (
    build_motion_meeting_user_create_test,
)

BaseClass: type = build_motion_meeting_user_create_test("motion_editor")


class MotionEditorCreateTest(BaseClass):
    __test__ = True
