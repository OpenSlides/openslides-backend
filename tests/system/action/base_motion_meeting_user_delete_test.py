from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


def build_motion_meeting_user_delete_test(collection: str) -> type[BaseActionTestCase]:
    class BaseMotionMeetingUserDeleteTest(BaseActionTestCase):
        action = f"{collection}.delete"
        __test__ = False

        def setUp(self) -> None:
            super().setUp()
            self.create_meeting()
            self.create_motion(1, 12)
            self.create_user_for_meeting(1)
            self.set_models(
                {
                    f"{collection}/111": {
                        "weight": 10,
                        "motion_id": 12,
                        "meeting_id": 1,
                        "meeting_user_id": 1,
                    },
                }
            )

        def test_delete_correct(self) -> None:
            response = self.request(self.action, {"id": 111})
            self.assert_status_code(response, 200)
            self.assert_model_not_exists(f"{collection}/111")

        def test_delete_wrong_id(self) -> None:
            response = self.request(self.action, {"id": 112})
            self.assert_status_code(response, 400)
            self.assert_model_exists(f"{collection}/111")
            self.assertEqual(
                f"Model '{collection}/112' does not exist.", response.json["message"]
            )

        def test_delete_no_permissions(self) -> None:
            self.base_permission_test({}, self.action, {"id": 111})

        def test_delete_permissions(self) -> None:
            self.base_permission_test(
                {}, self.action, {"id": 111}, Permissions.Motion.CAN_MANAGE_METADATA
            )

        def test_delete_permissions_locked_meeting(self) -> None:
            self.base_locked_out_superadmin_permission_test(
                {}, self.action, {"id": 111}
            )

    return BaseMotionMeetingUserDeleteTest
