from openslides_backend.permissions.management_levels import OrganizationManagementLevel

from .base import BasePresenterTestCase


class TestCheckDatabase(BasePresenterTestCase):
    def test_found_errors(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "test_foo"},
                "meeting/2": {"name": "test_bar"},
            }
        )
        status_code, data = self.request("check_database", {})
        assert status_code == 200
        assert data["ok"] is False
        assert "Meeting 1" in data["errors"]
        assert "meeting/1: Missing fields" in data["errors"]
        assert "Meeting 2" in data["errors"]
        assert "meeting/2: Missing fields" in data["errors"]

    def test_correct(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "active_meeting_ids": [1],
                    "organization_tag_ids": [1],
                },
                "organization_tag/1": {
                    "name": "TEST",
                    "color": "#eeeeee",
                    "organization_id": 1,
                },
                "committee/1": {"organization_id": 1},
                "meeting/1": {
                    "committee_id": 1,
                    "name": "Test",
                    "default_group_id": 1,
                    "admin_group_id": 2,
                    "motions_default_amendment_workflow_id": 1,
                    "motions_default_statute_amendment_workflow_id": 1,
                    "motions_default_workflow_id": 1,
                    "reference_projector_id": 1,
                    "projector_countdown_default_time": 60,
                    "projector_countdown_warning_time": 5,
                    "projector_ids": [1],
                    "group_ids": [1, 2],
                    "motion_state_ids": [1],
                    "motion_workflow_ids": [1],
                    "logo_$_id": None,
                    "font_$_id": [],
                    "default_projector_$_id": [],
                    "is_active_in_organization_id": 1,
                },
                "group/1": {
                    "meeting_id": 1,
                    "name": "default group",
                    "weight": 1,
                    "default_group_for_meeting_id": 1,
                },
                "group/2": {
                    "meeting_id": 1,
                    "name": "admin group",
                    "weight": 1,
                    "admin_group_for_meeting_id": 1,
                },
                "motion_workflow/1": {
                    "meeting_id": 1,
                    "name": "blup",
                    "first_state_id": 1,
                    "default_amendment_workflow_meeting_id": 1,
                    "default_statute_amendment_workflow_meeting_id": 1,
                    "default_workflow_meeting_id": 1,
                    "state_ids": [1],
                    "sequential_number": 1,
                },
                "motion_state/1": {
                    "css_class": "lightblue",
                    "meeting_id": 1,
                    "workflow_id": 1,
                    "name": "test",
                    "weight": 1,
                    "workflow_id": 1,
                    "first_state_of_workflow_id": 1,
                },
                "projector/1": {
                    "sequential_number": 1,
                    "meeting_id": 1,
                    "used_as_reference_projector_meeting_id": 1,
                    "name": "Default projector",
                    "used_as_default_$_in_meeting_id": [],
                },
            }
        )
        status_code, data = self.request("check_database", {})
        assert status_code == 200
        assert data["ok"] is True
        assert not data["errors"]

    def test_no_permissions(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "test_foo"},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
            }
        )
        status_code, data = self.request("check_database", {})
        assert status_code == 403
        assert "Missing permission: superadmin" in data["message"]
