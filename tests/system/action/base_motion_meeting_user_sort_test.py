from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


def build_motion_meeting_user_sort_test(collection: str) -> type[BaseActionTestCase]:
    class BaseMotionMeetingUserSortTest(BaseActionTestCase):
        action = f"{collection}.sort"
        __test__ = False

        def setUp(self) -> None:
            super().setUp()
            self.create_meeting()
            self.create_motion(1, 222)
            self.create_user_for_meeting(1)
            self.permission_test_models: dict[str, dict[str, Any]] = {
                f"{collection}/31": {
                    "motion_id": 222,
                    "meeting_id": 1,
                    "meeting_user_id": 1,
                },
                f"{collection}/32": {
                    "motion_id": 222,
                    "meeting_id": 1,
                    "meeting_user_id": 1,
                },
            }

        def test_sort_correct_1(self) -> None:
            self.set_models(self.permission_test_models)
            response = self.request(
                self.action,
                {"motion_id": 222, f"{collection}_ids": [32, 31]},
            )
            self.assert_status_code(response, 200)
            self.assert_model_exists(f"{collection}/31", {"weight": 2})
            self.assert_model_exists(f"{collection}/32", {"weight": 1})

        def test_sort_missing_model(self) -> None:
            self.set_models(
                {
                    f"{collection}/31": {
                        "motion_id": 222,
                        "meeting_id": 1,
                        "meeting_user_id": 1,
                    }
                }
            )
            response = self.request(
                self.action,
                {"motion_id": 222, f"{collection}_ids": [32, 31]},
            )
            self.assert_status_code(response, 400)
            self.assertEqual(
                f"{collection} sorting failed, because element {collection}/32 doesn't exist.",
                response.json["message"],
            )

        def test_sort_another_section_db(self) -> None:
            self.set_models(self.permission_test_models)
            self.set_models(
                {
                    f"{collection}/33": {
                        "motion_id": 222,
                        "meeting_id": 1,
                        "meeting_user_id": 1,
                    }
                }
            )
            response = self.request(
                self.action,
                {"motion_id": 222, f"{collection}_ids": [32, 31]},
            )
            self.assert_status_code(response, 400)
            self.assertEqual(
                f"{collection} sorting failed, because some elements were not included in the call.",
                response.json["message"],
            )

        def test_sort_no_permissions(self) -> None:
            self.base_permission_test(
                self.permission_test_models,
                self.action,
                {"motion_id": 222, f"{collection}_ids": [32, 31]},
            )

        def test_sort_permissions(self) -> None:
            self.base_permission_test(
                self.permission_test_models,
                self.action,
                {"motion_id": 222, f"{collection}_ids": [32, 31]},
                Permissions.Motion.CAN_MANAGE_METADATA,
            )

        def test_sort_permissions_locked_meeting(self) -> None:
            self.base_locked_out_superadmin_permission_test(
                self.permission_test_models,
                self.action,
                {"motion_id": 222, f"{collection}_ids": [32, 31]},
            )

    return BaseMotionMeetingUserSortTest
