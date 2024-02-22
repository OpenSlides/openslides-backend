from tests.system.action.base_motion_meeting_user_delete_test import (
    build_motion_meeting_user_delete_test,
)

BaseClass: type = build_motion_meeting_user_delete_test("motion_working_group_speaker")


class MotionWorkingGroupSpeakerDeleteTest(BaseClass):
    __test__ = True
