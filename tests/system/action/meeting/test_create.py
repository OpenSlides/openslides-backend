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
        self.assertIn("Creation of meeting/1: You try to set following required fields to an empty value: ['default_group_id', 'motions_default_amendment_workflow_id', 'motions_default_statute_amendment_workflow_id', 'motions_default_workflow_id']", response.json["message"])
        return {}

    def test_create_simple(self) -> None:
        self.basic_test(dict())

    def test_check_payload_fields(self) -> None:
        self.create_model("user/2")
        meeting = self.basic_test(
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
