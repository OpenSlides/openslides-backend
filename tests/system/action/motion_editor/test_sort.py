from tests.system.action.base_motion_meeting_user_sort_test import (
    build_motion_meeting_user_sort_test,
)

BaseClass: type = build_motion_meeting_user_sort_test("motion_editor")


class MotionEditorSortTest(BaseClass):
    __test__ = True
