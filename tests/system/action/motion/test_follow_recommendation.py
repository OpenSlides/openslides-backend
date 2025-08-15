from datetime import datetime
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionFollowRecommendationActionText(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_motion(1, 22)
        self.set_models(
            {
                "motion_state/76": {
                    "name": "test0",
                    "weight": 76,
                    "meeting_id": 1,
                    "workflow_id": 1,
                    "next_state_ids": [77],
                    "show_state_extension_field": True,
                    "show_recommendation_extension_field": True,
                },
                "motion_state/77": {
                    "name": "test1",
                    "weight": 77,
                    "meeting_id": 1,
                    "workflow_id": 1,
                    "first_state_of_workflow_id": 76,
                },
                "motion/22": {
                    "state_id": 77,
                    "recommendation_id": 76,
                    "recommendation_extension": "test_test_test",
                },
            }
        )

    def test_follow_recommendation_correct(self) -> None:
        check_time = datetime.now(ZoneInfo("UTC"))
        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.assert_model_exists(
            "motion/22",
            {
                "state_id": 76,
                "state_extension": "test_test_test",
            },
        )
        assert model.get("last_modified", datetime.fromtimestamp(0)) >= check_time
        self.assert_history_information(
            "motion/22", ["State set to {}", "motion_state/76"]
        )

    def test_follow_recommendation_not_neighbour(self) -> None:
        self.set_models({"motion_state/76": {"next_state_ids": None}})
        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "State '76' is not in next or previous states of the state '77'.",
            response.json["message"],
        )

    def test_follow_recommendation_missing_recommendation_id(self) -> None:
        self.set_models(
            {
                "motion/22": {
                    "recommendation_id": None,
                    "recommendation_extension": None,
                },
            }
        )
        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 200)

    def test_follow_recommendation_without_extension(self) -> None:
        self.set_models(
            {
                "motion/22": {"recommendation_extension": None},
            }
        )
        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/22",
            {
                "state_id": 76,
                "state_extension": None,
            },
        )

    def test_follow_recommendation_with_references(self) -> None:
        self.create_motion(1, 23)
        self.set_models(
            {
                "motion/22": {
                    "recommendation_extension": "[motion/23]",
                    "recommendation_extension_reference_ids": ["motion/23"],
                },
            }
        )
        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/22",
            {
                "state_id": 76,
                "state_extension": "[motion/23]",
                "state_extension_reference_ids": ["motion/23"],
            },
        )
        self.assert_model_exists(
            "motion/23",
            {"referenced_in_motion_state_extension_ids": [22]},
        )

    def test_follow_recommendation_without_references(self) -> None:
        self.create_motion(1, 23)
        self.set_models(
            {
                "motion/22": {
                    "state_extension": "[motion/23]",
                    "state_extension_reference_ids": ["motion/23"],
                    "recommendation_extension": "test",
                },
            }
        )
        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/22",
            {
                "state_id": 76,
                "state_extension": "test",
                "state_extension_reference_ids": None,
            },
        )
        self.assert_model_exists(
            "motion/23",
            {"referenced_in_motion_state_extension_ids": None},
        )

    def test_follow_recommendation_no_permission(self) -> None:
        self.base_permission_test(
            {},
            "motion.follow_recommendation",
            {"id": 22},
        )

    def test_follow_recommendation_permission(self) -> None:
        self.base_permission_test(
            {},
            "motion.follow_recommendation",
            {"id": 22},
            Permissions.Motion.CAN_MANAGE_METADATA,
        )

    def test_follow_recommendation_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "motion.follow_recommendation",
            {"id": 22},
        )
