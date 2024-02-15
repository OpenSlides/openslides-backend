from tests.system.action.base_motion_meeting_user_delete_test import (
    build_motion_meeting_user_delete_test,
)

BaseClass: type = build_motion_meeting_user_delete_test("motion_submitter")


class MotionSubmitterDeleteTest(BaseClass):
    __test__ = True

    def test_delete_correct(self) -> None:
        super().test_delete_correct()
        self.assert_history_information("motion/12", ["Submitters changed"])
