import time
from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionFollowRecommendationActionText(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_state/76": {
                "meeting_id": 1,
                "name": "test0",
                "motion_ids": [],
                "next_state_ids": [77],
                "previous_state_ids": [],
                "show_state_extension_field": True,
                "show_recommendation_extension_field": True,
            },
            "motion_state/77": {
                "meeting_id": 1,
                "name": "test1",
                "motion_ids": [22],
                "first_state_of_workflow_id": 76,
                "next_state_ids": [],
                "previous_state_ids": [76],
            },
            "motion/22": {
                "meeting_id": 1,
                "title": "test1",
                "state_id": 77,
                "recommendation_id": 76,
                "recommendation_extension": "test_test_test",
            },
        }

    def test_follow_recommendation_correct(self) -> None:
        check_time = round(time.time())
        self.set_models(
            {
                "motion_state/76": {
                    "meeting_id": 222,
                    "name": "test0",
                    "motion_ids": [],
                    "next_state_ids": [77],
                    "previous_state_ids": [],
                    "show_state_extension_field": True,
                    "show_recommendation_extension_field": True,
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
                    "recommendation_id": 76,
                    "recommendation_extension": "test_test_test",
                },
            }
        )
        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("state_extension") == "test_test_test"
        assert model.get("last_modified", 0) >= check_time
        self.assert_history_information(
            "motion/22", ["State set to {}", "motion_state/76"]
        )

    def test_follow_recommendation_not_neighbour(self) -> None:
        self.set_models(
            {
                "motion_state/76": {
                    "meeting_id": 222,
                    "name": "test0",
                    "motion_ids": [],
                    "next_state_ids": [],
                    "previous_state_ids": [],
                    "show_state_extension_field": True,
                    "show_recommendation_extension_field": True,
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "name": "test1",
                    "motion_ids": [22],
                    "first_state_of_workflow_id": 76,
                    "next_state_ids": [],
                    "previous_state_ids": [],
                },
                "motion/22": {
                    "meeting_id": 222,
                    "title": "test1",
                    "state_id": 77,
                    "recommendation_id": 76,
                    "recommendation_extension": "test_test_test",
                },
            }
        )
        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 400)
        assert (
            "State '76' is not in next or previous states of the state '77'."
            in response.json["message"]
        )

    def test_follow_recommendation_missing_recommendation_id(self) -> None:
        self.set_models(
            {
                "motion_state/76": {
                    "meeting_id": 222,
                    "name": "test0",
                    "motion_ids": [],
                    "next_state_ids": [77],
                    "previous_state_ids": [],
                    "show_state_extension_field": True,
                    "show_recommendation_extension_field": True,
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "name": "test1",
                    "motion_ids": [22],
                    "first_state_of_workflow_id": 76,
                    "next_state_ids": [],
                    "previous_state_ids": [76],
                },
                "motion/22": {"meeting_id": 222, "title": "test1", "state_id": 77},
            }
        )
        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 200)

    def test_follow_recommendation_without_extension(self) -> None:
        self.set_models(
            {
                "motion_state/76": {
                    "meeting_id": 222,
                    "next_state_ids": [77],
                    "show_state_extension_field": True,
                    "show_recommendation_extension_field": True,
                    "name": "test",
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "motion_ids": [22],
                    "first_state_of_workflow_id": 76,
                    "previous_state_ids": [76],
                },
                "motion/22": {
                    "meeting_id": 222,
                    "state_id": 77,
                    "recommendation_id": 76,
                },
            }
        )
        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("state_extension") is None

    def test_follow_recommendation_with_references(self) -> None:
        self.set_models(
            {
                "motion_state/76": {
                    "meeting_id": 222,
                    "next_state_ids": [77],
                    "show_state_extension_field": True,
                    "show_recommendation_extension_field": True,
                    "name": "test",
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "motion_ids": [22],
                    "first_state_of_workflow_id": 76,
                    "previous_state_ids": [76],
                },
                "motion/22": {
                    "meeting_id": 222,
                    "state_id": 77,
                    "recommendation_id": 76,
                    "recommendation_extension": "[motion/23]",
                    "recommendation_extension_reference_ids": ["motion/23"],
                },
                "motion/23": {
                    "meeting_id": 222,
                    "referenced_in_motion_recommendation_extension_ids": [22],
                },
            }
        )
        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("state_extension") == "[motion/23]"
        assert model.get("state_extension_reference_ids") == ["motion/23"]
        model = self.get_model("motion/23")
        assert model.get("referenced_in_motion_state_extension_ids") == [22]

    def test_follow_recommendation_without_references(self) -> None:
        self.set_models(
            {
                "motion_state/76": {
                    "meeting_id": 222,
                    "next_state_ids": [77],
                    "show_state_extension_field": True,
                    "show_recommendation_extension_field": True,
                    "name": "test",
                },
                "motion_state/77": {
                    "meeting_id": 222,
                    "motion_ids": [22],
                    "first_state_of_workflow_id": 76,
                    "previous_state_ids": [76],
                },
                "motion/22": {
                    "meeting_id": 222,
                    "state_id": 77,
                    "state_extension": "[motion/23]",
                    "state_extension_reference_ids": ["motion/23"],
                    "recommendation_id": 76,
                    "recommendation_extension": "test",
                },
                "motion/23": {
                    "meeting_id": 222,
                    "referenced_in_motion_state_extension_ids": [22],
                },
            }
        )
        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("state_extension") == "test"
        assert model.get("state_extension_reference_ids") == []
        model = self.get_model("motion/23")
        assert model.get("referenced_in_motion_state_extension_ids") == []

    def test_follow_recommendation_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.follow_recommendation",
            {"id": 22},
        )

    def test_follow_recommendation_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.follow_recommendation",
            {"id": 22},
            Permissions.Motion.CAN_MANAGE_METADATA,
        )

    def test_follow_recommendation_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion.follow_recommendation",
            {"id": 22},
        )
