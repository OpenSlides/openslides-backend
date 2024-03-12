from tests.system.action.base_motion_meeting_user_create_test import (
    build_motion_meeting_user_create_test,
)

BaseClass: type = build_motion_meeting_user_create_test("motion_submitter")


class MotionSubmitterCreateTest(BaseClass):
    __test__ = True

    def test_create(self) -> None:
        super().test_create()
        self.assert_history_information("motion/357", ["Submitters changed"])
