from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


def build_motion_meeting_user_create_test(collection: str) -> type[BaseActionTestCase]:
    class BaseMotionMeetingUserCreateTest(BaseActionTestCase):
        action = f"{collection}.create"
        __test__ = False

        def setUp(self) -> None:
            super().setUp()
            self.create_meeting()
            self.create_motion(1, 357)
            self.create_user_for_meeting(1)

        def test_create(self) -> None:
            response = self.request(
                self.action,
                {"motion_id": 357, "meeting_user_id": 1, "weight": 100},
            )
            self.assert_status_code(response, 200)
            self.assert_model_exists(
                f"{collection}/1",
                {"motion_id": 357, "meeting_user_id": 1, "weight": 100},
            )

        def test_create_default_weight(self) -> None:
            self.create_user_for_meeting(1)
            self.set_models(
                {
                    f"{collection}/1": {
                        "meeting_user_id": 1,
                        "motion_id": 357,
                        "weight": 100,
                        "meeting_id": 1,
                    },
                }
            )
            response = self.request(
                self.action, {"motion_id": 357, "meeting_user_id": 2}
            )
            self.assert_status_code(response, 200)
            self.assert_model_exists(
                f"{collection}/2",
                {"motion_id": 357, "meeting_user_id": 2, "weight": 101},
            )

        def test_create_weight_double_action(self) -> None:
            self.create_user_for_meeting(1)
            self.create_user_for_meeting(1)
            response = self.request_multi(
                self.action,
                [
                    {"motion_id": 357, "meeting_user_id": 1},
                    {"motion_id": 357, "meeting_user_id": 2},
                    {"motion_id": 357, "meeting_user_id": 3},
                ],
            )
            self.assert_status_code(response, 200)
            self.assert_model_exists(
                f"{collection}/1", {"weight": 1, "meeting_user_id": 1}
            )
            self.assert_model_exists(
                f"{collection}/2", {"weight": 2, "meeting_user_id": 2}
            )
            self.assert_model_exists(
                f"{collection}/3", {"weight": 3, "meeting_user_id": 3}
            )

        def test_create_not_unique(self) -> None:
            self.set_models(
                {
                    f"{collection}/12": {
                        "motion_id": 357,
                        "meeting_user_id": 1,
                        "meeting_id": 1,
                    },
                }
            )
            response = self.request(
                self.action, {"motion_id": 357, "meeting_user_id": 1}
            )
            self.assert_status_code(response, 400)
            self.assertEqual(
                "(meeting_user_id, motion_id) must be unique.", response.json["message"]
            )

        def test_create_empty_data(self) -> None:
            response = self.request(self.action, {})
            self.assert_status_code(response, 400)
            self.assertEqual(
                f"Action {self.action}: data must contain ['meeting_user_id', 'motion_id'] properties",
                response.json["message"],
            )

        def test_create_wrong_field(self) -> None:
            response = self.request(
                self.action,
                {
                    "motion_id": 357,
                    "meeting_user_id": 1,
                    "wrong_field": "text_AefohteiF8",
                },
            )
            self.assert_status_code(response, 400)
            self.assertEqual(
                f"Action {self.action}: data must not contain {{'wrong_field'}} properties",
                response.json["message"],
            )

        def test_create_not_matching_meeting_ids(self) -> None:
            self.create_meeting(4)
            self.create_user_for_meeting(4)
            response = self.request(
                self.action, {"motion_id": 357, "meeting_user_id": 2}
            )
            self.assert_status_code(response, 400)
            self.assertEqual(
                "The following models do not belong to meeting 1: ['user/3']",
                response.json["message"],
            )

        def test_create_no_permissions(self) -> None:
            self.base_permission_test(
                {},
                self.action,
                {"motion_id": 357, "meeting_user_id": 1},
            )

        def test_create_permissions(self) -> None:
            self.base_permission_test(
                {},
                self.action,
                {"motion_id": 357, "meeting_user_id": 1},
                Permissions.Motion.CAN_MANAGE_METADATA,
            )

        def test_create_permissions_locked_out(self) -> None:
            self.base_permission_test(
                {},
                self.action,
                {"motion_id": 357, "meeting_user_id": 1},
                Permissions.Motion.CAN_MANAGE_METADATA,
                lock_out_calling_user=True,
                fail=True,
            )

        def test_create_permissions_locked_meeting(self) -> None:
            self.base_locked_out_superadmin_permission_test(
                {},
                self.action,
                {"motion_id": 357, "meeting_user_id": 1},
            )

    return BaseMotionMeetingUserCreateTest
