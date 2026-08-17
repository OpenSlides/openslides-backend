from openslides_backend.models.models import Poll
from tests.system.action.base import BaseActionTestCase


class MeetingSettingsSystemTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_update_poll_default_group_ids(self) -> None:
        self.set_models(
            {
                "meeting/1": {"motion_poll_config_id": 1},
                "group/2": {"used_in_meeting_poll_default_ids": [1]},
                "meeting_poll_default/1": {"meeting_id": 1},
            }
        )
        response = self.request(
            "meeting.update", {"id": 1, "motion_poll_default_group_ids": [2, 3]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("group/1", {"used_in_meeting_poll_default_ids": None})
        self.assert_model_exists("group/2", {"used_in_meeting_poll_default_ids": [1]})
        self.assert_model_exists("group/3", {"used_in_meeting_poll_default_ids": [1]})
        self.assert_model_exists("meeting_poll_default/1", {"group_ids": [2, 3]})

    def test_set_poll_default_group_ids_not_in_meeting(self) -> None:
        self.create_meeting(4)
        response = self.request(
            "meeting.update", {"id": 1, "motion_poll_default_group_ids": [4]}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The following models do not belong to meeting 1: ['group/4']",
            response.json["message"],
        )
        self.assert_model_exists("meeting/1", {"poll_default_ids": None})

    def test_poll_default_projector(self) -> None:
        self.set_models({"projector/2": {"meeting_id": 1, "name": "Projector 2"}})
        response = self.request(
            "meeting.update", {"id": 1, "default_projector_assignment_poll_ids": [2]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"default_projector_assignment_poll_ids": [2]}
        )
        self.assert_model_exists(
            "projector/1",
            {"used_as_default_projector_for_assignment_poll_in_meeting_id": None},
        )
        self.assert_model_exists(
            "projector/2",
            {"used_as_default_projector_for_assignment_poll_in_meeting_id": 1},
        )

    def test_poll_default_projector_not_in_meeting(self) -> None:
        self.create_meeting(4)
        response = self.request(
            "meeting.update", {"id": 1, "default_projector_assignment_poll_ids": [4]}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The following models do not belong to meeting 1: ['projector/4']",
            response.json["message"],
        )
        self.assert_model_exists(
            "meeting/1", {"default_projector_assignment_poll_ids": [1]}
        )

    def base_test_meeting_poll_default_settings(self) -> None:
        data = {
            "sort_result_by_votes": False,
            "visibility": "named",
            "allow_abstain": False,
            "allow_nota": True,
            "strike_out": True,
            "onehundred_percent_base": Poll.ONEHUNDRED_PERCENT_BASE_CAST,
            "group_ids": [1],
            "display_chart": "test",
        }
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                **{
                    f"{poll_type}_poll_default_{field_name}": value
                    for poll_type in ("assignment", "motion", "topic")
                    for field_name, value in data.items()
                },
            },
        )
        self.assert_status_code(response, 200)
        for poll_type, id_ in {"assignment": 1, "motion": 2, "topic": 3}.items():
            self.assert_model_exists(
                f"meeting_poll_default/{id_}",
                {
                    "meeting_id": 1,
                    f"used_as_{poll_type}_poll_config_in_meeting_id": 1,
                    **data,
                },
            )
        self.assert_model_exists(
            "group/1",
            {"used_in_meeting_poll_default_ids": [1, 2, 3]},
        )

    def test_create_meeting_poll_default_settings(self) -> None:
        self.base_test_meeting_poll_default_settings()
        self.assert_model_exists(
            "meeting/1",
            {
                "poll_default_ids": [1, 2, 3],
                "assignment_poll_config_id": 1,
                "motion_poll_config_id": 2,
                "topic_poll_config_id": 3,
            },
        )

    def test_update_meeting_poll_default_settings(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "assignment_poll_config_id": 1,
                    "motion_poll_config_id": 2,
                    "topic_poll_config_id": 3,
                },
                "meeting_poll_default/1": {"meeting_id": 1},
                "meeting_poll_default/2": {"meeting_id": 1},
                "meeting_poll_default/3": {"meeting_id": 1},
            }
        )
        self.base_test_meeting_poll_default_settings()

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
