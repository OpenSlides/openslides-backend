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

    def test_delete_without_sllos_deletion(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_ids": [2],
                    "meeting_user_ids": [3, 33],
                    "list_of_speakers_default_structure_level_time": 300,
                    "is_active_in_organization_id": 1,
                    "structure_level_list_of_speakers_ids": [42],
                    "speaker_ids": [23, 233],
                    "structure_level_ids": [4],
                },
                "group/1": {"meeting_id": 1, "meeting_user_ids": [3, 33]},
                "list_of_speakers/2": {
                    "meeting_id": 1,
                    "structure_level_list_of_speakers_ids": [42],
                    "speaker_ids": [23, 233],
                },
                "meeting_user/3": {
                    "meeting_id": 1,
                    "group_ids": [1],
                    "speaker_ids": [23],
                },
                "speaker/23": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 2,
                    "meeting_user_id": 3,
                    "structure_level_list_of_speakers_id": 42,
                },
                "meeting_user/33": {
                    "meeting_id": 1,
                    "group_ids": [1],
                    "speaker_ids": [233],
                },
                "speaker/233": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 2,
                    "meeting_user_id": 33,
                    "structure_level_list_of_speakers_id": 42,
                },
                "structure_level/4": {
                    "meeting_id": 1,
                    "name": "level 1",
                    "meeting_user_ids": [3, 33],
                    "structure_level_list_of_speakers_ids": [42],
                },
                "structure_level_list_of_speakers/42": {
                    "list_of_speakers_id": 2,
                    "speaker_ids": [23, 233],
                    "meeting_id": 1,
                    "structure_level_id": 4,
                    "initial_time": 300,
                    "remaining_time": 300,
                },
            }
        )
        response = self.request("speaker.delete", {"id": 23})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/23")
        self.assert_model_exists(
            "structure_level_list_of_speakers/42", {"speaker_ids": [233]}
        )

    def sllos_single_user_setup(self, **sllos_times: int) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_ids": [2],
                    "meeting_user_ids": [3],
                    "list_of_speakers_default_structure_level_time": 300,
                    "is_active_in_organization_id": 1,
                    "structure_level_list_of_speakers_ids": [42],
                    "speaker_ids": [23],
                    "structure_level_ids": [4],
                },
                "group/1": {"meeting_id": 1, "meeting_user_ids": [3]},
                "list_of_speakers/2": {
                    "meeting_id": 1,
                    "structure_level_list_of_speakers_ids": [42],
                    "speaker_ids": [23],
                },
                "meeting_user/3": {
                    "meeting_id": 1,
                    "group_ids": [1],
                    "speaker_ids": [23],
                },
                "structure_level/4": {
                    "meeting_id": 1,
                    "name": "level 1",
                    "meeting_user_ids": [3],
                    "structure_level_list_of_speakers_ids": [42],
                },
                "speaker/23": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 2,
                    "meeting_user_id": 3,
                    "structure_level_list_of_speakers_id": 42,
                },
                "structure_level_list_of_speakers/42": {
                    "list_of_speakers_id": 2,
                    "speaker_ids": [23],
                    "meeting_id": 1,
                    "structure_level_id": 4,
                    **sllos_times,
                },
            }
        )

    def test_delete_without_sllos_deletion_2(self) -> None:
        self.sllos_single_user_setup(
            initial_time=300, additional_time=60, remaining_time=300
        )
        response = self.request("speaker.delete", {"id": 23})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/23")
        self.assert_model_exists(
            "structure_level_list_of_speakers/42", {"speaker_ids": []}
        )

    def test_delete_without_sllos_deletion_3(self) -> None:
        self.sllos_single_user_setup(
            initial_time=300, current_start_time=12345678, remaining_time=300
        )
        response = self.request("speaker.delete", {"id": 23})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/23")
        self.assert_model_exists(
            "structure_level_list_of_speakers/42", {"speaker_ids": []}
        )

    def test_delete_without_sllos_deletion_4(self) -> None:
        self.sllos_single_user_setup(initial_time=300, remaining_time=100)
        response = self.request("speaker.delete", {"id": 23})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/23")
        self.assert_model_exists(
            "structure_level_list_of_speakers/42", {"speaker_ids": []}
        )

    def test_delete_with_sllos_deletion(self) -> None:
        self.sllos_single_user_setup(initial_time=300, remaining_time=300)
        response = self.request("speaker.delete", {"id": 23})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/23")
        self.assert_model_deleted("structure_level_list_of_speakers/42")
