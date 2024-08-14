import time
from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionResetStateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_workflow/1": {
                "meeting_id": 1,
                "name": "test1",
                "state_ids": [76, 77],
                "first_state_id": 76,
            },
            "motion_state/76": {
                "meeting_id": 1,
                "name": "test0",
                "motion_ids": [],
                "workflow_id": 1,
                "first_state_of_workflow_id": 1,
                "set_number": True,
            },
            "motion_state/77": {
                "meeting_id": 1,
                "name": "test1",
                "motion_ids": [22],
                "workflow_id": 1,
            },
            "motion/22": {
                "meeting_id": 1,
                "title": "test1",
                "state_id": 77,
                "number": "001",
            },
        }

    def test_reset_state_correct(self) -> None:
        check_time = round(time.time())
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_workflow/1": {
                    "meeting_id": 222,
                    "name": "test1",
                    "state_ids": [76, 77],
                    "first_state_id": 76,
                },
                "motion_state/76": {
                    "meeting_id": 222,
                    "name": "test0",
                    "motion_ids": [],
                    "workflow_id": 1,
                    "first_state_of_workflow_id": 1,
                    "set_number": True,
                    "set_workflow_timestamp": True,
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "name": "test1",
                    "motion_ids": [22],
                    "workflow_id": 1,
                },
                "motion/22": {
                    "meeting_id": 222,
                    "title": "test1",
                    "state_id": 77,
                    "number": "001",
                    "created": 1687339000,
                },
            }
        )
        response = self.request("motion.reset_state", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("number") == "001"
        assert model.get("last_modified", 0) >= check_time
        assert model.get("workflow_timestamp") == model.get("last_modified")
        assert model.get("created") == 1687339000

    def test_reset_state_correct_number_value(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_workflow/1": {
                    "name": "test1",
                    "state_ids": [76, 77],
                    "first_state_id": 76,
                    "meeting_id": 222,
                },
                "motion_state/76": {
                    "name": "test0",
                    "motion_ids": [],
                    "workflow_id": 1,
                    "first_state_of_workflow_id": 1,
                    "set_number": True,
                    "meeting_id": 222,
                    "set_workflow_timestamp": False,
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "name": "test1",
                    "motion_ids": [22],
                    "workflow_id": 1,
                },
                "motion/22": {
                    "meeting_id": 222,
                    "title": "test1",
                    "state_id": 77,
                    "number_value": 23,
                    "workflow_timestamp": 1111111,
                },
            }
        )
        response = self.request("motion.reset_state", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("number_value") == 23
        assert model.get("workflow_timestamp") is None

    def test_reset_state_missing_first_state(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_workflow/1": {
                    "meeting_id": 222,
                    "name": "test1",
                    "state_ids": [76, 77],
                },
                "motion_state/76": {
                    "meeting_id": 222,
                    "name": "test0",
                    "motion_ids": [],
                    "workflow_id": 1,
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "name": "test1",
                    "motion_ids": [22],
                    "workflow_id": 1,
                },
                "motion/22": {"meeting_id": 222, "title": "test1", "state_id": 77},
            }
        )
        response = self.request("motion.reset_state", {"id": 22})
        self.assert_status_code(response, 400)
        self.assertIn(" has no first_state_id.", response.json["message"])

    def test_reset_state_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.reset_state",
            {"id": 22},
        )

    def test_reset_state_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.reset_state",
            {"id": 22},
            Permissions.Motion.CAN_MANAGE_METADATA,
        )

    def test_reset_state_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion.reset_state",
            {"id": 22},
        )
