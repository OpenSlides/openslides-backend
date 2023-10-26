from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase

DEFAULT_PASSWORD = "password"


class SpeakerDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: Dict[str, Dict[str, Any]] = {
            "meeting/1": {
                "speaker_ids": [890],
                "is_active_in_organization_id": 1,
                "meeting_user_ids": [7],
            },
            "user/7": {
                "username": "test_username1",
                "meeting_user_ids": [7],
                "is_active": True,
                "default_password": DEFAULT_PASSWORD,
                "password": self.auth.hash(DEFAULT_PASSWORD),
            },
            "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
            "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 1},
            "speaker/890": {
                "meeting_user_id": 7,
                "list_of_speakers_id": 23,
                "meeting_id": 1,
            },
        }

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "speaker_ids": [890],
                    "is_active_in_organization_id": 1,
                },
                "user/7": {
                    "username": "test_username1",
                    "meeting_user_ids": [7],
                },
                "meeting_user/7": {
                    "meeting_id": 111,
                    "user_id": 7,
                    "speaker_ids": [890],
                },
                "list_of_speakers/23": {"speaker_ids": [890]},
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/890")
        self.assert_model_exists("meeting_user/7", {"speaker_ids": []})

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "speaker_ids": [890],
                    "is_active_in_organization_id": 1,
                },
                "user/7": {
                    "username": "test_username1",
                    "meeting_user_ids": [7],
                },
                "meeting_user/7": {
                    "meeting_id": 111,
                    "user_id": 7,
                    "speaker_ids": [890],
                },
                "list_of_speakers/23": {"speaker_ids": [890]},
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("speaker.delete", {"id": 889})
        self.assert_status_code(response, 400)
        self.assert_model_exists("speaker/890")

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models, "speaker.delete", {"id": 890}
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "speaker.delete",
            {"id": 890},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_delete_self(self) -> None:
        self.create_meeting()
        self.user_id = 7
        self.set_models(self.permission_test_models)
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)

    def test_delete_correct_on_closed_los(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "speaker_ids": [890],
                    "is_active_in_organization_id": 1,
                },
                "user/7": {
                    "username": "test_username1",
                    "meeting_user_ids": [7],
                },
                "meeting_user/7": {
                    "meeting_id": 111,
                    "user_id": 7,
                    "speaker_ids": [890],
                },
                "list_of_speakers/23": {"speaker_ids": [890], "closed": True},
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/890")

    def test_delete_with_removed_user(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "speaker_ids": [890],
                    "is_active_in_organization_id": 1,
                },
                "user/7": {
                    "username": "test_username1",
                    "meeting_user_ids": [7],
                },
                "meeting_user/7": {
                    "meeting_id": 111,
                    "user_id": 7,
                    "speaker_ids": [890],
                    "group_ids": [],
                },
                "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 111},
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/890")
        self.assert_model_exists("meeting_user/7", {"speaker_ids": []})

    def test_delete_with_deleted_user(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "speaker_ids": [890],
                    "is_active_in_organization_id": 1,
                },
                "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 111},
                "speaker/890": {
                    "list_of_speakers_id": 23,
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/890")
