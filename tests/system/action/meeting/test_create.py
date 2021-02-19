from typing import Any, Dict

from tests.system.action.base import BaseActionTestCase


class MeetingCreateActionTest(BaseActionTestCase):
    def basic_test(self, datapart: Dict[str, Any]) -> Dict[str, Any]:
        self.create_model("committee/1", {"name": "test_committee"})
        self.create_model("group/1")
        response = self.request(
            "meeting.create",
            {
                "name": "test_name",
                "committee_id": 1,
                "welcome_title": "test_wel_title",
                **datapart,
            },
        )
        # Annotation: Creation and testing will be fixed with Issue492/pull request486
        self.assert_status_code(response, 400)
        self.assertIn(
            "XCreation of meeting/1: You try to set following required fields to an empty value: ['default_group_id', 'motions_default_amendment_workflow_id', 'motions_default_statute_amendment_workflow_id', 'motions_default_workflow_id']",
            response.json["message"],
        )
        return {}

    def test_create_simple(self) -> None:
        self.basic_test(dict())
        self.assert_model_exists(
            "meeting/1",
            {
                "name": "test_name",
                "committee_id": 1,
                "group_ids": [2, 3, 4, 5, 6],
                "default_group_id": 2,
                "admin_group_id": 3,
                "motion_workflow_ids": [1],
                "motions_default_workflow_id": 1,
                "motions_default_amendment_workflow_id": 1,
                "motions_default_statute_amendment_workflow_id": 1,
                "motion_state_ids": [1, 2, 3, 4],
            },
        )
        self.assert_model_exists("group/2", {"name": "Default"})
        self.assert_model_exists("group/3", {"name": "Admin"})
        self.assert_model_exists("group/4", {"name": "Delegates"})
        self.assert_model_exists("group/5", {"name": "Staff"})
        self.assert_model_exists("group/6", {"name": "Committees"})
        self.assert_model_exists(
            "motion_workflow/1",
            {
                "name": "Simple Workflow",
                "meeting_id": 1,
                "default_workflow_meeting_id": 1,
                "default_amendment_workflow_meeting_id": 1,
                "default_statute_amendment_workflow_meeting_id": 1,
                "state_ids": [1, 2, 3, 4],
                "first_state_id": 4,
            },
        )
        self.assert_model_exists(
            "motion_state/1",
            {
                "name": "accepted",
                "previous_state_ids": [4],
                "meeting_id": 1,
                "workflow_id": 1,
            },
        )
        self.assert_model_exists(
            "motion_state/2", {"name": "rejected", "previous_state_ids": [4]}
        )
        self.assert_model_exists(
            "motion_state/3", {"name": "not_decided", "previous_state_ids": [4]}
        )
        self.assert_model_exists(
            "motion_state/4", {"name": "submitted", "next_state_ids": [1, 2, 3]}
        )

    def test_check_payload_fields(self) -> None:
        self.create_model("user/2")
        self.basic_test(
            {
                "welcome_text": "htXiSgbj",
                "description": "RRfnzxHA",
                "location": "LSFHPTgE",
                "start_time": 1608120653,
                "end_time": 1608121653,
                "url_name": "JWdYZqDX",
                "enable_anonymous": False,
                "guest_ids": [2],
            }
        )
