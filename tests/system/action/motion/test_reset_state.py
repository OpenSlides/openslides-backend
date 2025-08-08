from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionResetStateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_workflow/1": {"first_state_id": 76},
            "motion_state/76": {
                "name": "test0",
                "weight": 76,
                "meeting_id": 1,
                "workflow_id": 1,
                "first_state_of_workflow_id": 1,
                "set_number": True,
            },
            "motion_state/77": {
                "name": "test1",
                "weight": 77,
                "meeting_id": 1,
                "workflow_id": 1,
            },
            "motion/22": {
                "meeting_id": 1,
                "title": "test1",
                "sequential_number": 22,
                "state_id": 77,
                "number": "001",
            },
        }

    def set_test_models(self) -> None:
        self.create_motion(222, 22)
        self.set_models(
            {
                "motion_workflow/1": {
                    "name": "test1",
                    "meeting_id": 222,
                    "state_ids": [76, 77],
                    "first_state_id": 76,
                    "sequential_number": 1,
                },
                "motion_state/76": {
                    "name": "test0",
                    "weight": 76,
                    "meeting_id": 222,
                    "workflow_id": 1,
                    "first_state_of_workflow_id": 1,
                    "set_number": True,
                    "set_workflow_timestamp": True,
                },
                "motion_state/77": {
                    "name": "test1",
                    "weight": 77,
                    "meeting_id": 222,
                    "motion_ids": [22],
                    "workflow_id": 1,
                },
                "motion/22": {"title": "test1", "state_id": 77},
            }
        )

    def test_reset_state_correct(self) -> None:
        check_time = datetime.now(ZoneInfo("UTC"))
        self.set_test_models()
        self.set_models(
            {
                "motion/22": {
                    "number": "001",
                    "created": datetime.fromtimestamp(1687339000),
                },
            }
        )
        response = self.request("motion.reset_state", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("number") == "001"
        assert (
            model.get("last_modified", datetime.fromtimestamp(0, ZoneInfo("UTC")))
            >= check_time
        )
        assert model.get("workflow_timestamp") == model.get("last_modified")
        assert model.get("created") == datetime.fromtimestamp(
            1687339000, ZoneInfo("UTC")
        )

    def test_reset_state_correct_number_value(self) -> None:
        self.set_test_models()
        self.set_models(
            {
                "motion_state/76": {"set_workflow_timestamp": False},
                "motion/22": {
                    "number_value": 23,
                    "workflow_timestamp": datetime.fromtimestamp(1111111),
                },
            }
        )
        response = self.request("motion.reset_state", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("number_value") == 23
        assert model.get("workflow_timestamp") is None

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
