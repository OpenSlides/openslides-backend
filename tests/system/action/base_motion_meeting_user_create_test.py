from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


def build_motion_meeting_user_create_test(collection: str) -> type[BaseActionTestCase]:
    class BaseMotionMeetingUserCreateTest(BaseActionTestCase):
        action = f"{collection}.create"
        __test__ = False

        def setUp(self) -> None:
            super().setUp()
            self.create_meeting(111)
            self.permission_test_models: dict[str, dict[str, Any]] = {
                "meeting/1": {"meeting_user_ids": [78]},
                "motion/357": {
                    "title": "title_YIDYXmKj",
                    "meeting_id": 1,
                },
                "user/78": {
                    "username": "username_loetzbfg",
                    "meeting_ids": [1],
                    "meeting_user_ids": [78],
                },
                "meeting_user/78": {"meeting_id": 111, "user_id": 78},
            }

        def test_create(self) -> None:
            self.set_models(
                {
                    "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                    "user/78": {"username": "username_loetzbfg", "meeting_ids": [111]},
                    "meeting_user/79": {"meeting_id": 111, "user_id": 78},
                }
            )
            response = self.request(
                self.action,
                {"motion_id": 357, "meeting_user_id": 79, "weight": 100},
            )
            self.assert_status_code(response, 200)
            model = self.get_model(f"{collection}/1")
            assert model.get("motion_id") == 357
            assert model.get("meeting_user_id") == 79
            assert model.get("weight") == 100

        def test_create_default_weight(self) -> None:
            self.set_models(
                {
                    "meeting/111": {
                        "meeting_user_ids": [78, 79],
                    },
                    "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                    "user/78": {
                        "username": "username_loetzbfg",
                        "meeting_ids": [111],
                        "meeting_user_ids": [78],
                    },
                    "user/79": {
                        "username": "username_wuumpoop",
                        "meeting_ids": [111],
                    },
                    f"{collection}/1": {
                        "meeting_user_id": 78,
                        "motion_id": 357,
                        "weight": 100,
                        "meeting_id": 111,
                    },
                    "meeting_user/78": {
                        "meeting_id": 111,
                        "user_id": 78,
                        f"{collection}_ids": [1],
                    },
                    "meeting_user/79": {"meeting_id": 111, "user_id": 79},
                }
            )
            response = self.request(
                self.action, {"motion_id": 357, "meeting_user_id": 79}
            )
            self.assert_status_code(response, 200)
            model = self.get_model(f"{collection}/2")
            assert model.get("motion_id") == 357
            assert model.get("meeting_user_id") == 79
            assert model.get("weight") == 101

        def test_create_weight_double_action(self) -> None:
            self.set_models(
                {
                    "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                    "user/78": {"username": "username_loetzbfg", "meeting_ids": [111]},
                    "user/89": {"username": "username_ghjiuen2", "meeting_ids": [111]},
                    "user/93": {"username": "username_husztw", "meeting_ids": [111]},
                    "meeting_user/78": {"meeting_id": 111, "user_id": 78},
                    "meeting_user/89": {"meeting_id": 111, "user_id": 89},
                    "meeting_user/93": {"meeting_id": 111, "user_id": 93},
                }
            )
            response = self.request_multi(
                self.action,
                [
                    {"motion_id": 357, "meeting_user_id": 78},
                    {"motion_id": 357, "meeting_user_id": 89},
                    {"motion_id": 357, "meeting_user_id": 93},
                ],
            )
            self.assert_status_code(response, 200)
            self.assert_model_exists(
                f"{collection}/1", {"weight": 1, "meeting_user_id": 78}
            )
            self.assert_model_exists(
                f"{collection}/2", {"weight": 2, "meeting_user_id": 89}
            )
            self.assert_model_exists(
                f"{collection}/3", {"weight": 3, "meeting_user_id": 93}
            )

        def test_create_not_unique(self) -> None:
            self.set_models(
                {
                    "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                    "user/78": {"username": "username_loetzbfg", "meeting_ids": [111]},
                    "meeting_user/78": {"meeting_id": 111, "user_id": 78},
                    f"{collection}/12": {
                        "motion_id": 357,
                        "meeting_user_id": 78,
                        "meeting_id": 111,
                    },
                }
            )
            response = self.request(
                self.action, {"motion_id": 357, "meeting_user_id": 78}
            )
            self.assert_status_code(response, 400)
            assert "(meeting_user_id, motion_id) must be unique." in response.json.get(
                "message", ""
            )

        def test_create_empty_data(self) -> None:
            response = self.request(self.action, {})
            self.assert_status_code(response, 400)
            self.assertIn(
                "data must contain ['meeting_user_id', 'motion_id'] properties",
                response.json["message"],
            )

        def test_create_wrong_field(self) -> None:
            response = self.request(
                self.action,
                {
                    "motion_id": 357,
                    "meeting_user_id": 78,
                    "wrong_field": "text_AefohteiF8",
                },
            )
            self.assert_status_code(response, 400)
            self.assertIn(
                "data must not contain {'wrong_field'} properties",
                response.json["message"],
            )

        def test_create_not_matching_meeting_ids(self) -> None:
            self.create_meeting(112)
            self.set_models(
                {
                    "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                    "user/78": {"username": "username_loetzbfg", "meeting_ids": [112]},
                    "meeting_user/78": {"meeting_id": 111, "user_id": 78},
                }
            )
            response = self.request(
                self.action, {"motion_id": 357, "meeting_user_id": 78}
            )
            self.assert_status_code(response, 400)
            self.assertIn(
                "The following models do not belong to meeting 111: ['user/78']",
                response.json["message"],
            )

        def test_create_no_permissions(self) -> None:
            self.base_permission_test(
                self.permission_test_models,
                self.action,
                {"motion_id": 357, "meeting_user_id": 78},
            )

        def test_create_permissions(self) -> None:
            self.base_permission_test(
                self.permission_test_models,
                self.action,
                {"motion_id": 357, "meeting_user_id": 78},
                Permissions.Motion.CAN_MANAGE_METADATA,
            )

        def test_create_permissions_locked_out(self) -> None:
            self.base_permission_test(
                self.permission_test_models,
                self.action,
                {"motion_id": 357, "meeting_user_id": 78},
                Permissions.Motion.CAN_MANAGE_METADATA,
                lock_out_calling_user=True,
                fail=True,
            )

        def test_create_permissions_locked_meeting(self) -> None:
            self.base_locked_out_superadmin_permission_test(
                self.permission_test_models,
                self.action,
                {"motion_id": 357, "meeting_user_id": 78},
            )

    return BaseMotionMeetingUserCreateTest
