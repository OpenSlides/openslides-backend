from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


def build_motion_meeting_user_sort_test(collection: str) -> type[BaseActionTestCase]:
    class BaseMotionMeetingUserSortTest(BaseActionTestCase):
        action = f"{collection}.sort"
        __test__ = False

        def setUp(self) -> None:
            super().setUp()
            self.permission_test_models: dict[str, dict[str, Any]] = {
                "motion/222": {"meeting_id": 1},
                f"{collection}/31": {"motion_id": 222, "meeting_id": 1},
                f"{collection}/32": {"motion_id": 222, "meeting_id": 1},
            }

        def test_sort_correct_1(self) -> None:
            self.set_models(
                {
                    "meeting/13": {"is_active_in_organization_id": 1},
                    "motion/222": {"meeting_id": 13},
                    f"{collection}/31": {"motion_id": 222, "meeting_id": 13},
                    f"{collection}/32": {"motion_id": 222, "meeting_id": 13},
                }
            )
            response = self.request(
                self.action,
                {"motion_id": 222, f"{collection}_ids": [32, 31]},
            )
            self.assert_status_code(response, 200)
            model_31 = self.get_model(f"{collection}/31")
            assert model_31.get("weight") == 2
            model_32 = self.get_model(f"{collection}/32")
            assert model_32.get("weight") == 1

        def test_sort_missing_model(self) -> None:
            self.set_models(
                {
                    "meeting/13": {"is_active_in_organization_id": 1},
                    "motion/222": {"meeting_id": 13},
                    f"{collection}/31": {"motion_id": 222, "meeting_id": 13},
                }
            )
            response = self.request(
                self.action,
                {"motion_id": 222, f"{collection}_ids": [32, 31]},
            )
            self.assert_status_code(response, 400)
            assert (
                f"{collection} sorting failed, because element {collection}/32 doesn't exist."
                in response.json["message"]
            )

        def test_sort_another_section_db(self) -> None:
            self.set_models(
                {
                    "meeting/13": {"is_active_in_organization_id": 1},
                    "motion/222": {"meeting_id": 13},
                    f"{collection}/31": {"motion_id": 222, "meeting_id": 13},
                    f"{collection}/32": {"motion_id": 222, "meeting_id": 13},
                    f"{collection}/33": {"motion_id": 222, "meeting_id": 13},
                }
            )
            response = self.request(
                self.action,
                {"motion_id": 222, f"{collection}_ids": [32, 31]},
            )
            self.assert_status_code(response, 400)
            assert (
                f"{collection} sorting failed, because some elements were not included in the call."
                in response.json["message"]
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

    return BaseMotionMeetingUserSortTest
