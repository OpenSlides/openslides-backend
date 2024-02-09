from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSetSupportSelfActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion/1": {
                "title": "motion_1",
                "meeting_id": 1,
                "state_id": 1,
                "supporter_meeting_user_ids": [],
            },
            "meeting/1": {
                "name": "name_meeting_1",
                "motion_ids": [1],
                "motions_supporters_min_amount": 1,
                "is_active_in_organization_id": 1,
            },
            "motion_state/1": {
                "name": "state_1",
                "allow_support": True,
                "motion_ids": [1],
                "meeting_id": 1,
            },
        }

    def test_meeting_support_system_deactivated(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 0,
                    "is_active_in_organization_id": 1,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": False,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion.set_support_self", {"motion_id": 1, "support": True}
        )
        self.assert_status_code(response, 400)
        assert "Motion supporters system deactivated." in response.json.get(
            "message", ""
        )

    def test_state_doesnt_allow_support(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                    "is_active_in_organization_id": 1,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": False,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion.set_support_self", {"motion_id": 1, "support": True}
        )
        self.assert_status_code(response, 400)
        assert "The state does not allow support." in response.json["message"]

    def test_support(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_meeting_user_ids": [],
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                    "is_active_in_organization_id": 1,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": True,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion.set_support_self", {"motion_id": 1, "support": True}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("supporter_meeting_user_ids") == [1]
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": 1, "user_id": 1, "supported_motion_ids": [1]},
        )

    def test_unsupport(self) -> None:
        self.set_models(
            {
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "supported_motion_ids": [1],
                },
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_meeting_user_ids": [1],
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                    "is_active_in_organization_id": 1,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": True,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion.set_support_self", {"motion_id": 1, "support": False}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("supporter_meeting_user_ids") == []
        self.assert_model_exists("meeting_user/1", {"supported_motion_ids": []})

    def test_unsupport_no_change(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_meeting_user_ids": [],
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                    "is_active_in_organization_id": 1,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": True,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion.set_support_self", {"motion_id": 1, "support": False}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("supporter_meeting_user_ids") == []

    def test_set_support_self_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.set_support_self",
            {"motion_id": 1, "support": True},
        )

    def test_set_support_self_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.set_support_self",
            {"motion_id": 1, "support": True},
            Permissions.Motion.CAN_SUPPORT,
        )
