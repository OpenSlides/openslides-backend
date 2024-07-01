from tests.system.action.base_motion_meeting_user_update_test import (
    build_motion_meeting_user_update_test,
)

BaseClass: type = build_motion_meeting_user_update_test("motion_working_group_speaker")


class MotionWorkingGroupSpeakerUpdateTest(BaseClass):
    __test__ = True
