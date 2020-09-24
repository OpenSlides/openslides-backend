from tests.system.action.base import BaseActionTestCase


class MeetingSettingsSystemTest(BaseActionTestCase):
    def test_group_ids(self) -> None:
        self.create_model("meeting/1", {"motion_poll_default_group_ids": [1]})
        self.create_model("group/1", {"used_as_motion_poll_default_id": 1})
        self.create_model(
            "group/2", {"name": "2", "used_as_motion_poll_default_id": None}
        )
        self.create_model("group/3", {"used_as_motion_poll_default_id": None})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.update",
                    "data": [{"id": 1, "motion_poll_default_group_ids": [2, 3]}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
        self.assertEqual(meeting["motion_poll_default_group_ids"], [2, 3])
        group1 = self.get_model("group/1")
        self.assertEqual(group1.get("used_as_motion_poll_default_id"), None)
        group2 = self.get_model("group/2")
        self.assertEqual(group2["used_as_motion_poll_default_id"], 1)
        group3 = self.get_model("group/3")
        self.assertEqual(group3["used_as_motion_poll_default_id"], 1)

    def test_html_field(self) -> None:
        self.create_model("meeting/1", {"welcome_text": "Hi"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.update",
                    "data": [{"id": 1, "welcome_text": "<iframe>"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
        self.assertEqual(meeting["welcome_text"], "&lt;iframe&gt;")
