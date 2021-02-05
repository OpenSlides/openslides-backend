import time

from tests.system.action.base import BaseActionTestCase


class MotionFollowRecommendationActionText(BaseActionTestCase):
    def test_follow_recommendation_correct(self) -> None:
        check_time = round(time.time())
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_state/76",
            {
                "meeting_id": 222,
                "name": "test0",
                "motion_ids": [],
                "next_state_ids": [77],
                "previous_state_ids": [],
                "show_state_extension_field": True,
                "show_recommendation_extension_field": True,
            },
        )
        self.create_model(
            "motion_state/77",
            {
                "meeting_id": 222,
                "name": "test1",
                "motion_ids": [22],
                "first_state_of_workflow_id": 76,
                "next_state_ids": [],
                "previous_state_ids": [76],
            },
        )
        self.create_model(
            "motion/22",
            {
                "meeting_id": 222,
                "title": "test1",
                "state_id": 77,
                "recommendation_id": 76,
                "recommendation_extension": "test_test_test",
            },
        )
        response = self.client.post(
            "/",
            json=[{"action": "motion.follow_recommendation", "data": [{"id": 22}]}],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("state_extension") == "test_test_test"
        assert model.get("last_modified", 0) >= check_time

    def test_follow_recommendation_not_neighbour(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_state/76",
            {
                "meeting_id": 222,
                "name": "test0",
                "motion_ids": [],
                "next_state_ids": [],
                "previous_state_ids": [],
                "show_state_extension_field": True,
                "show_recommendation_extension_field": True,
            },
        )
        self.create_model(
            "motion_state/77",
            {
                "meeting_id": 222,
                "name": "test1",
                "motion_ids": [22],
                "first_state_of_workflow_id": 76,
                "next_state_ids": [],
                "previous_state_ids": [],
            },
        )
        self.create_model(
            "motion/22",
            {
                "meeting_id": 222,
                "title": "test1",
                "state_id": 77,
                "recommendation_id": 76,
                "recommendation_extension": "test_test_test",
            },
        )
        response = self.client.post(
            "/",
            json=[{"action": "motion.follow_recommendation", "data": [{"id": 22}]}],
        )
        self.assert_status_code(response, 400)
        assert (
            "State '76' is not in next or previous states of the state '77'."
            in response.json["message"]
        )

    def test_follow_recommendation_missing_recommendation_id(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_state/76",
            {
                "meeting_id": 222,
                "name": "test0",
                "motion_ids": [],
                "next_state_ids": [77],
                "previous_state_ids": [],
                "show_state_extension_field": True,
                "show_recommendation_extension_field": True,
            },
        )
        self.create_model(
            "motion_state/77",
            {
                "meeting_id": 222,
                "name": "test1",
                "motion_ids": [22],
                "first_state_of_workflow_id": 76,
                "next_state_ids": [],
                "previous_state_ids": [76],
            },
        )
        self.create_model(
            "motion/22", {"meeting_id": 222, "title": "test1", "state_id": 77}
        )
        response = self.client.post(
            "/",
            json=[{"action": "motion.follow_recommendation", "data": [{"id": 22}]}],
        )
        self.assert_status_code(response, 200)
