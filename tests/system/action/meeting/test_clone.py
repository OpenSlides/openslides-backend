from typing import Any, Dict
from unittest.mock import MagicMock

from openslides_backend.permissions.management_levels import CommitteeManagementLevel
from tests.system.action.base import BaseActionTestCase


class MeetingClone(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: Dict[str, Dict[str, Any]] = {
            "organization/1": {"active_meeting_ids": [1]},
            "committee/1": {"organization_id": 1},
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
                "logo_$_id": None,
                "font_$_id": [],
                "default_projector_$_id": None,
                "is_active_in_organization_id": 1,
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
                "weight": 1,
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

    def test_clone_without_users(self) -> None:
        self.set_models(self.test_models)

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "committee_id": 1,
                "name": "Test - Copy",
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
                "logo_$_id": None,
                "font_$_id": [],
                "default_projector_$_id": None,
            },
        )

    def test_clone_with_users(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["group/1"]["user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "meeting_ids": [1],
                }
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "group_$_ids": ["1", "2"],
                "group_$1_ids": [1],
                "group_$2_ids": [2],
                "meeting_ids": [1, 2],
            },
        )
        self.assert_model_exists("meeting/1", {"user_ids": [1]})
        self.assert_model_exists("meeting/2", {"user_ids": [1]})

    def test_clone_with_personal_note(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["personal_note_ids"] = [1]
        self.test_models["group/1"]["user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "personal_note_$_ids": ["1"],
                    "personal_note_$1_ids": [1],
                },
                "personal_note/1": {
                    "note": "test note",
                    "user_id": 1,
                    "meeting_id": 1,
                },
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "personal_note_$_ids": ["1", "2"],
                "personal_note_$1_ids": [1],
                "personal_note_$2_ids": [2],
            },
        )

    def test_clone_with_option(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["option_ids"] = [1]
        self.test_models["group/1"]["user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "option_$_ids": ["1"],
                    "option_$1_ids": [1],
                },
                "option/1": {"content_object_id": "user/1", "meeting_id": 1},
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "option_$_ids": ["1", "2"],
                "option_$1_ids": [1],
                "option_$2_ids": [2],
            },
        )

    def test_clone_with_mediafile(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["mediafile_ids"] = [1]
        self.test_models["group/1"]["user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "meeting_ids": [1],
                },
                "mediafile/1": {
                    "meeting_id": 1,
                    "attachment_ids": [],
                    "used_as_font_$_in_meeting_id": [],
                    "used_as_logo_$_in_meeting_id": [],
                    "mimetype": "text/plain",
                },
            }
        )
        self.set_models(self.test_models)
        self.media.duplicate_mediafile = MagicMock()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.media.duplicate_mediafile.assert_called_with(1, 2)

    def test_clone_with_organization_tag(self) -> None:
        self.test_models["meeting/1"]["organization_tag_ids"] = [1]
        self.set_models(
            {
                "organization_tag/1": {
                    "name": "Test",
                    "color": "#ffffff",
                    "tagged_ids": ["meeting/1"],
                }
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"organization_tag_ids": [1]})

    def test_limit_of_meetings_error(self) -> None:
        self.test_models["organization/1"]["limit_of_meetings"] = 1
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "You cannot clone an active meeting, because you reached your limit of 1 active meetings.",
            response.json["message"],
        )

    def test_limit_of_meetings_archived_meeting(self) -> None:
        self.test_models["organization/1"]["limit_of_meetings"] = 1
        self.test_models["organization/1"]["active_meeting_ids"] = [3]
        self.test_models["meeting/1"]["is_active_in_organization_id"] = None
        self.set_models(self.test_models)

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"is_active_in_organization_id": None})
        self.assert_model_exists("organization/1", {"active_meeting_ids": [3]})

    def test_limit_of_meetings_ok(self) -> None:
        self.test_models["organization/1"]["limit_of_meetings"] = 2
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        organization = self.get_model("organization/1")
        self.assertCountEqual(organization["active_meeting_ids"], [1, 2])

    def test_create_clone(self) -> None:
        self.set_models(
            {
                "organization/1": {},
                "committee/1": {"organization_id": 1, "user_ids": [2, 3]},
                "user/2": {"committee_ids": [1]},
                "user/3": {"committee_ids": [1]},
            }
        )
        response = self.request(
            "meeting.create",
            {
                "committee_id": 1,
                "name": "meeting",
                "description": "",
                "location": "",
                "start_time": 1633039200,
                "end_time": 1633039200,
                "user_ids": [2, 3],
                "admin_ids": [],
                "organization_tag_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_meeting_name_too_long(self) -> None:
        long_name = "0123456789" * 10
        self.test_models["meeting/1"]["name"] = long_name
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"name": long_name})

    def test_permissions_both_okay(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "committee/2": {"organization_id": 1},
                "user/1": {
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_$2_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_ids": [1, 2],
                    "organization_management_level": None,
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"is_active_in_organization_id": 1, "committee_id": 1}
        )
        self.assert_model_exists(
            "meeting/2", {"is_active_in_organization_id": 1, "committee_id": 2}
        )

    def test_permissions_oml_can_manage(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "committee/2": {"organization_id": 1},
                "user/1": {
                    "organization_management_level": "can_manage_organization",
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"is_active_in_organization_id": 1, "committee_id": 1}
        )
        self.assert_model_exists(
            "meeting/2", {"is_active_in_organization_id": 1, "committee_id": 2}
        )

    def test_permissions_missing_meeting_committee_permission(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "committee/2": {"organization_id": 1},
                "user/1": {
                    "committee_$2_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_ids": [2],
                    "organization_management_level": None,
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 2})
        self.assert_status_code(response, 403)
        self.assertIn(
            "Missing CommitteeManagementLevel: can_manage for committee 1",
            response.json["message"],
        )

    def test_permissions_missing_payload_committee_permission(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "committee/2": {"organization_id": 1},
                "user/1": {
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_ids": [1],
                    "organization_management_level": None,
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 2})
        self.assert_status_code(response, 403)
        self.assertIn(
            "Missing CommitteeManagementLevel: can_manage for committee 2",
            response.json["message"],
        )
