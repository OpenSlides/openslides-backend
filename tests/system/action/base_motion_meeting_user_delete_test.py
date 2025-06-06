from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


def build_motion_meeting_user_delete_test(collection: str) -> type[BaseActionTestCase]:
    class BaseMotionMeetingUserDeleteTest(BaseActionTestCase):
        action = f"{collection}.delete"
        __test__ = False

        def setUp(self) -> None:
            super().setUp()
            self.permission_test_models: dict[str, dict[str, Any]] = {
                "meeting/1": {
                    f"{collection}_ids": [111],
                    "is_active_in_organization_id": 1,
                },
                "motion/12": {
                    "meeting_id": 1,
                    "title": "test2",
                    "submitter_ids": [111],
                },
                f"{collection}/111": {
                    "weight": 10,
                    "motion_id": 12,
                    "meeting_id": 1,
                },
            }

        def test_delete_correct(self) -> None:
            self.create_meeting(98)
            self.set_models(
                {
                    "meeting/98": {
                        f"{collection}_ids": [111],
                    },
                    "motion/12": {
                        "meeting_id": 98,
                        "title": "test2",
                        "submitter_ids": [111],
                    },
                    f"{collection}/111": {
                        "weight": 10,
                        "motion_id": 12,
                        "meeting_id": 98,
                    },
                }
            )
            response = self.request(self.action, {"id": 111})
            self.assert_status_code(response, 200)
            self.assert_model_not_exists(f"{collection}/111")

        def test_delete_wrong_id(self) -> None:
            self.create_model(f"{collection}/112", {"weight": 10})
            response = self.request(self.action, {"id": 111})
            self.assert_status_code(response, 400)
            self.assert_model_exists(f"{collection}/112")

        def test_delete_no_permissions(self) -> None:
            self.base_permission_test(
                self.permission_test_models,
                self.action,
                {"id": 111},
            )

        def test_delete_permissions(self) -> None:
            self.base_permission_test(
                self.permission_test_models,
                self.action,
                {"id": 111},
                Permissions.Motion.CAN_MANAGE_METADATA,
            )

        def test_delete_permissions_locked_meeting(self) -> None:
            self.base_locked_out_superadmin_permission_test(
                self.permission_test_models,
                self.action,
                {"id": 111},
            )

    return BaseMotionMeetingUserDeleteTest
