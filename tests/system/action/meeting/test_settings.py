from tests.system.action.base import BaseActionTestCase


class MeetingSettingsSystemTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_group_ids(self) -> None:
        self.set_models({"group/1": {"used_as_motion_poll_default_id": 1}})
        response = self.request(
            "meeting.update", {"id": 1, "motion_poll_default_group_ids": [2, 3]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"motion_poll_default_group_ids": [2, 3]})
        self.assert_model_exists("group/1", {"used_as_motion_poll_default_id": None})
        self.assert_model_exists("group/2", {"used_as_motion_poll_default_id": 1})
        self.assert_model_exists("group/3", {"used_as_motion_poll_default_id": 1})

    def test_html_field_iframe(self) -> None:
        response = self.request(
            "meeting.update", {"id": 1, "welcome_text": '<iframe allow="yes">'}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1",
            {
                "welcome_text": '<iframe sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe>',
            },
        )

    def test_html_field_iframe_attributes(self) -> None:
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "welcome_text": '<iframe allow="yes" allowfullscreen=true allowpaymentrequest=true csp="test" fetchpriority="high" sandbox="broken" referrerpolicy="link">',
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1",
            {
                "welcome_text": '<iframe sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe>',
            },
        )

    def test_html_field_script(self) -> None:
        response = self.request(
            "meeting.update",
            {"id": 1, "welcome_text": '<script>alert("TEST");</script>'},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"welcome_text": '&lt;script&gt;alert("TEST");&lt;/script&gt;'}
        )
