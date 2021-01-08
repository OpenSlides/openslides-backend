from typing import Any, Dict

from tests.system.action.base import BaseActionTestCase


class MeetingCreateActionTest(BaseActionTestCase):
    def basic_test(self, datapart: Dict[str, Any]) -> Dict[str, Any]:
        self.create_model("committee/1", {"name": "test_committee"})
        self.create_model("group/1", {})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.create",
                    "data": [
                        {
                            "name": "test_name",
                            "committee_id": 1,
                            "welcome_title": "test_wel_title",
                            **datapart,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
        assert meeting.get("name") == "test_name"
        assert meeting.get("committee_id") == 1
        return meeting

    def test_create_simple(self) -> None:
        self.basic_test(dict())

    def test_check_payload_fields(self) -> None:
        self.create_model("user/2", {})
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
        assert meeting.get("welcome_text") == "htXiSgbj"
        assert meeting.get("description") == "RRfnzxHA"
        assert meeting.get("location") == "LSFHPTgE"
        assert meeting.get("start_time") == 1608120653
        assert meeting.get("end_time") == 1608121653
        assert meeting.get("url_name") == "JWdYZqDX"
        assert meeting.get("enable_anonymous") is False
        assert meeting.get("guest_ids") == [2]
        assert meeting.get("user_ids") == [2]
        user_2 = self.get_model("user/2")
        assert user_2.get("guest_meeting_ids") == [1]
