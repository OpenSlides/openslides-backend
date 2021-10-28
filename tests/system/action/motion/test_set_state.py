import time
from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSetStateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model: Dict[str, Dict[str, Any]] = {
            "motion_state/76": {
                "meeting_id": 1,
                "name": "test0",
                "motion_ids": [],
                "next_state_ids": [77],
                "previous_state_ids": [],
                "allow_submitter_edit": True,
            },
            "motion_state/77": {
                "meeting_id": 1,
                "name": "test1",
                "motion_ids": [22],
                "first_state_of_workflow_id": 76,
                "next_state_ids": [],
                "previous_state_ids": [76],
                "allow_submitter_edit": True,
            },
            "motion/22": {
                "meeting_id": 1,
                "title": "test1",
                "state_id": 77,
                "number_value": 23,
                "submitter_ids": [12],
            },
            "motion_submitter/12": {
                "meeting_id": 1,
                "motion_id": 22,
                "user_id": 1,
            },
        }

    def test_set_state_correct_previous_state(self) -> None:
        check_time = round(time.time())
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_state/76": {
                    "meeting_id": 222,
                    "name": "test0",
                    "motion_ids": [],
                    "next_state_ids": [77],
                    "previous_state_ids": [],
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "name": "test1",
                    "motion_ids": [22],
                    "first_state_of_workflow_id": 76,
                    "next_state_ids": [],
                    "previous_state_ids": [76],
                },
                "motion/22": {
                    "meeting_id": 222,
                    "title": "test1",
                    "state_id": 77,
                    "number_value": 23,
                },
            }
        )
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("number_value") == 23
        assert model.get("last_modified", 0) >= check_time

    def test_set_state_correct_next_state(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_state/76": {
                    "meeting_id": 222,
                    "name": "test0",
                    "motion_ids": [],
                    "next_state_ids": [],
                    "previous_state_ids": [77],
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "name": "test1",
                    "motion_ids": [22],
                    "first_state_of_workflow_id": 76,
                    "next_state_ids": [76],
                    "previous_state_ids": [],
                },
                "motion/22": {
                    "meeting_id": 222,
                    "title": "test1",
                    "state_id": 77,
                    "number": "A021",
                },
            }
        )
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("number") == "A021"

    def test_set_state_wrong_not_in_next_or_previous(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_state/76": {
                    "meeting_id": 222,
                    "name": "test0",
                    "motion_ids": [],
                    "next_state_ids": [],
                    "previous_state_ids": [],
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "name": "test1",
                    "motion_ids": [22],
                    "first_state_of_workflow_id": 76,
                    "next_state_ids": [],
                    "previous_state_ids": [],
                },
                "motion/22": {"meeting_id": 222, "title": "test1", "state_id": 77},
            }
        )
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 400)
        self.assertIn(
            "State '76' is not in next or previous states of the state '77'.",
            response.json["message"],
        )

    def test_set_state_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "motion.set_state",
            {"id": 22, "state_id": 76},
        )

    def test_set_state_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "motion.set_state",
            {"id": 22, "state_id": 76},
            Permissions.Motion.CAN_MANAGE_METADATA,
        )

    def test_set_state_permission_submitter(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.permission_test_model["motion_submitter/12"]["user_id"] = self.user_id
        self.set_models(self.permission_test_model)
        self.set_user_groups(self.user_id, [3])
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 200)
