from typing import Any

from openslides_backend.action.actions.user.delegation_based_restriction_mixin import (
    DelegationBasedRestriction,
)
from openslides_backend.permissions.base_classes import Permission
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase

DEFAULT_PASSWORD = "password"


class SpeakerDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
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

    def create_delegator_test_data(
        self,
        is_present: bool = False,
        is_delegator: bool = False,
        perm: Permission = Permissions.ListOfSpeakers.CAN_BE_SPEAKER,
        delegator_setting: DelegationBasedRestriction = "users_forbid_delegator_in_list_of_speakers",
    ) -> None:
        self.create_meeting(1)
        self.user_id = 7
        self.set_models(self.permission_test_models)
        self.login(self.user_id)
        self.set_models(
            {
                "meeting_user/7": {"group_ids": [1]},
                "meeting/1": {
                    "meeting_user_ids": [7],
                    delegator_setting: True,
                },
                "group/1": {"meeting_user_ids": [7]},
            }
        )
        if is_delegator:
            self.create_user("delegatee", [1])
            self.set_models(
                {
                    "meeting_user/7": {"vote_delegated_to_id": 1},
                    "meeting_user/1": {"vote_delegations_from_ids": [7]},
                }
            )
        self.set_organization_management_level(None)
        self.set_group_permissions(1, [perm])
        self.set_user_groups(7, [1])

    def test_delegator_setting_with_no_delegation(self) -> None:
        self.create_delegator_test_data()
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/890")

    def test_delegator_setting_with_delegation(self) -> None:
        self.create_delegator_test_data(is_delegator=True)
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action speaker.delete. Missing Permission: list_of_speakers.can_manage"
        )

    def test_delegator_setting_with_motion_manager_delegation(
        self,
    ) -> None:
        self.create_delegator_test_data(
            is_delegator=True, perm=Permissions.ListOfSpeakers.CAN_MANAGE
        )
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/890")

    def test_with_irrelevant_delegator_setting(self) -> None:
        self.create_delegator_test_data(
            is_delegator=True, delegator_setting="users_forbid_delegator_as_submitter"
        )
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("speaker/890")
