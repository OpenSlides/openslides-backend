import time

from tests.system.action.base import BaseActionTestCase


class MotionSetStateActionTest(BaseActionTestCase):
    def test_set_state_correct_previous_state(self) -> None:
        check_time = round(time.time())
        self.set_models(
            {
                "meeting/222": {"name": "name_SNLGsvIV"},
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
                "meeting/222": {"name": "name_SNLGsvIV"},
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
                "meeting/222": {"name": "name_SNLGsvIV"},
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
