from tests.system.action.base import BaseActionTestCase


class MotionCreateForwarded(BaseActionTestCase):
    def test_correct_origin_id_set(self) -> None:
        self.set_models(
            {
                "meeting/221": {"name": "name_XDAddEAW", "committee_id": 53},
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "motions_default_workflow_id": 12,
                    "committee_id": 52,
                },
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {"name": "name_state34", "meeting_id": 222},
                "motion/12": {
                    "title": "title_FcnPUXJB",
                    "meeting_id": 221,
                    "state_id": 34,
                },
                "committee/52": {"name": "name_EeKbwxpa"},
                "committee/53": {
                    "name": "name_auSwgfJC",
                    "forward_to_committee_ids": [52],
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "origin_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/13")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("origin_id") == 12

    def test_correct_origin_id_wrong_1(self) -> None:
        self.set_models(
            {
                "meeting/221": {"name": "name_XDAddEAW", "committee_id": 53},
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "motions_default_workflow_id": 12,
                    "committee_id": 52,
                },
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {"name": "name_state34", "meeting_id": 222},
                "motion/12": {
                    "title": "title_FcnPUXJB",
                    "meeting_id": 221,
                    "state_id": 34,
                },
                "committee/52": {"name": "name_EeKbwxpa"},
                "committee/53": {
                    "name": "name_auSwgfJC",
                    "forward_to_committee_ids": [],
                },
            }
        )
        response = self.request(
            "motion.create_forwarded",
            {
                "title": "test_Xcdfgee",
                "text": "text",
                "meeting_id": 222,
                "origin_id": 12,
            },
        )
        self.assert_status_code(response, 400)
        assert "Committee id 52 not in []" in response.json["message"]
