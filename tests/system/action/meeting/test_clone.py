from tests.system.action.base import BaseActionTestCase


class MeetingClone(BaseActionTestCase):
    def test_clone_without_users(self) -> None:
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {
                    "committee_id": 1,
                    "name": "Test",
                    "admin_group_id": 1,
                    "default_group_id": 1,
                    "motions_default_amendment_workflow_id": 1,
                    "motions_default_statute_amendment_workflow_id": 1,
                    "motions_default_workflow_id": 1,
                    "reference_projector_id": 1,
                    "projector_countdown_default_time": 60,
                    "projector_countdown_warning_time": 5,
                    "projector_ids": [1],
                    "group_ids": [1],
                    "motion_state_ids": [1],
                    "motion_workflow_ids": [1],
                    "logo_$_id": [],
                    "font_$_id": [],
                    "default_projector_$_id": [],
                },
                "group/1": {
                    "meeting_id": 1,
                    "name": "testgroup",
                    "admin_group_for_meeting_id": 1,
                    "default_group_for_meeting_id": 1,
                },
                "motion_workflow/1": {
                    "meeting_id": 1,
                    "name": "blup",
                    "first_state_id": 1,
                    "default_amendment_workflow_meeting_id": 1,
                    "default_statute_amendment_workflow_meeting_id": 1,
                    "default_workflow_meeting_id": 1,
                    "state_ids": [1],
                },
                "motion_state/1": {
                    "css_class": "lightblue",
                    "meeting_id": 1,
                    "workflow_id": 1,
                    "name": "test",
                    "workflow_id": 1,
                    "first_state_of_workflow_id": 1,
                },
                "projector/1": {
                    "meeting_id": 1,
                    "used_as_reference_projector_meeting_id": 1,
                    "name": "Default projector",
                    "used_as_default_$_in_meeting_id": [],
                },
            }
        )

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "committee_id": 1,
                "name": "Test",
                "admin_group_id": 2,
                "default_group_id": 2,
                "motions_default_amendment_workflow_id": 2,
                "motions_default_statute_amendment_workflow_id": 2,
                "motions_default_workflow_id": 2,
                "reference_projector_id": 2,
                "projector_countdown_default_time": 60,
                "projector_countdown_warning_time": 5,
                "projector_ids": [2],
                "group_ids": [2],
                "motion_state_ids": [2],
                "motion_workflow_ids": [2],
                "logo_$_id": [],
                "font_$_id": [],
                "default_projector_$_id": [],
            },
        )

    def test_clone_with_users(self) -> None:
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {
                    "committee_id": 1,
                    "name": "Test",
                    "admin_group_id": 1,
                    "default_group_id": 1,
                    "motions_default_amendment_workflow_id": 1,
                    "motions_default_statute_amendment_workflow_id": 1,
                    "motions_default_workflow_id": 1,
                    "reference_projector_id": 1,
                    "projector_countdown_default_time": 60,
                    "projector_countdown_warning_time": 5,
                    "projector_ids": [1],
                    "group_ids": [1],
                    "motion_state_ids": [1],
                    "motion_workflow_ids": [1],
                    "logo_$_id": [],
                    "font_$_id": [],
                    "default_projector_$_id": [],
                    "user_ids": [1],
                },
                "group/1": {
                    "meeting_id": 1,
                    "name": "testgroup",
                    "admin_group_for_meeting_id": 1,
                    "default_group_for_meeting_id": 1,
                    "user_ids": [1],
                },
                "user/1": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                },
                "motion_workflow/1": {
                    "meeting_id": 1,
                    "name": "blup",
                    "first_state_id": 1,
                    "default_amendment_workflow_meeting_id": 1,
                    "default_statute_amendment_workflow_meeting_id": 1,
                    "default_workflow_meeting_id": 1,
                    "state_ids": [1],
                },
                "motion_state/1": {
                    "css_class": "lightblue",
                    "meeting_id": 1,
                    "workflow_id": 1,
                    "name": "test",
                    "workflow_id": 1,
                    "first_state_of_workflow_id": 1,
                },
                "projector/1": {
                    "meeting_id": 1,
                    "used_as_reference_projector_meeting_id": 1,
                    "name": "Default projector",
                    "used_as_default_$_in_meeting_id": [],
                },
            }
        )

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
