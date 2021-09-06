import base64
from typing import Any, Dict
from unittest.mock import MagicMock

from tests.system.action.base import BaseActionTestCase


class MeetingClone(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: Dict[str, Dict[str, Any]] = {
            "organization/1": {},
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

    def test_clone_without_users(self) -> None:
        self.set_models(self.test_models)

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
        self.media.download_mediafile = MagicMock(return_value=b"testtesttest")
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.media.download_mediafile.assert_called_with(1)
        self.media.upload_mediafile.assert_called_with(
            base64.b64encode(b"testtesttest"), 2, "text/plain"
        )

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
