from tests.system.action.base import BaseActionTestCase


class MeetingSettingsSystemTest(BaseActionTestCase):
    def test_group_ids(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "motion_poll_default_group_ids": [1],
                    "is_active_in_organization_id": 1,
                    "language": "en",
                    "committee_id": 1,
                },
                "group/1": {"used_as_motion_poll_default_id": 1},
                "group/2": {"name": "2", "used_as_motion_poll_default_id": None},
                "group/3": {"used_as_motion_poll_default_id": None},
            }
        )
        response = self.request(
            "meeting.update", {"id": 1, "motion_poll_default_group_ids": [2, 3]}
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

    def test_html_field_iframe(self) -> None:
        self.create_model(
            "meeting/1",
            {
                "welcome_text": "Hi",
                "is_active_in_organization_id": 1,
                "language": "en",
                "committee_id": 1,
            },
        )
        response = self.request(
            "meeting.update", {"id": 1, "welcome_text": '<iframe allow="yes">'}
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
        self.assertEqual(
            meeting["welcome_text"],
            '<iframe sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe>',
        )

    def test_html_field_iframe_attributes(self) -> None:
        self.create_model(
            "meeting/1",
            {
                "welcome_text": "Hi",
                "is_active_in_organization_id": 1,
                "language": "en",
                "committee_id": 1,
            },
        )
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "welcome_text": '<iframe allow="yes" allowfullscreen=true allowpaymentrequest=true csp="test" fetchpriority="high" sandbox="broken" referrerpolicy="link">',
            },
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
        self.assertEqual(
            meeting["welcome_text"],
            '<iframe sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe>',
        )

    def test_html_field_script(self) -> None:
        self.create_model(
            "meeting/1",
            {
                "welcome_text": "Hi",
                "is_active_in_organization_id": 1,
                "language": "en",
                "committee_id": 1,
            },
        )
        response = self.request(
            "meeting.update",
            {"id": 1, "welcome_text": '<script>alert("TEST");</script>'},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"welcome_text": '&lt;script&gt;alert("TEST");&lt;/script&gt;'}
        )
