from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionResetStateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_motion(1, 22)
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_workflow/1": {"first_state_id": 76},
            "motion_state/76": {
                "meeting_id": 1,
                "name": "test0",
                "workflow_id": 1,
                "first_state_of_workflow_id": 1,
                "weight": 76,
                "set_number": True,
            },
            "motion_state/77": {
                "meeting_id": 1,
                "name": "test1",
                "workflow_id": 1,
                "weight": 77,
            },
            "motion/22": {
                "title": "test1",
                "state_id": 77,
                "number": "001",
            },
        }

    def test_reset_state_correct(self) -> None:
        check_time = datetime.now(ZoneInfo("UTC"))
        self.permission_test_models["motion/22"].update(
            {"number": "001", "created": datetime.fromtimestamp(1687339000)}
        )
        self.permission_test_models["motion_state/76"].update(
            {"set_workflow_timestamp": True}
        )
        self.set_models(self.permission_test_models)

        response = self.request("motion.reset_state", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.assert_model_exists(
            "motion/22",
            {
                "state_id": 76,
                "number": "001",
                "created": datetime.fromtimestamp(1687339000, ZoneInfo("UTC")),
            },
        )
        model_last_modified = model.get(
            "last_modified", datetime.fromtimestamp(0, ZoneInfo("UTC"))
        )
        assert model_last_modified >= check_time
        assert model.get("workflow_timestamp") == model_last_modified

    def test_reset_state_correct_number_value(self) -> None:
        self.permission_test_models["motion/22"].update(
            {"number_value": 23, "workflow_timestamp": datetime.fromtimestamp(1111111)}
        )
        self.set_models(self.permission_test_models)

        response = self.request("motion.reset_state", {"id": 22})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/22",
            {"state_id": 76, "number_value": 23, "workflow_timestamp": None},
        )

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
