from math import floor
from time import time
from typing import Any

from openslides_backend.action.mixins.delegation_based_restriction_mixin import (
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
        self.assert_model_not_exists("speaker/890")
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

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "speaker.delete",
            {"id": 890},
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
        self.assert_model_not_exists("speaker/890")

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
        self.assert_model_not_exists("speaker/890")
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
        self.assert_model_not_exists("speaker/890")

    def create_delegator_test_data(
        self,
        is_present: bool = False,
        is_delegator: bool = False,
        perm: Permission = Permissions.ListOfSpeakers.CAN_BE_SPEAKER,
        delegator_setting: DelegationBasedRestriction = "users_forbid_delegator_in_list_of_speakers",
        disable_delegations: bool = False,
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
                    **(
                        {}
                        if disable_delegations
                        else {"users_enable_vote_delegations": True}
                    ),
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
        self.assert_model_not_exists("speaker/890")

    def test_delegator_setting_with_delegation(self) -> None:
        self.create_delegator_test_data(is_delegator=True)
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action speaker.delete. Missing Permission: list_of_speakers.can_manage"
        )

    def test_delegator_setting_with_delegation_delegations_turned_off(self) -> None:
        self.create_delegator_test_data(is_delegator=True, disable_delegations=True)
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)

    def test_delegator_setting_with_motion_manager_delegation(
        self,
    ) -> None:
        self.create_delegator_test_data(
            is_delegator=True, perm=Permissions.ListOfSpeakers.CAN_MANAGE
        )
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("speaker/890")

    def test_with_irrelevant_delegator_setting(self) -> None:
        self.create_delegator_test_data(
            is_delegator=True, delegator_setting="users_forbid_delegator_as_submitter"
        )
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("speaker/890")

    def test_with_active_structure_level_speaker(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "speaker_ids": [890],
                    "is_active_in_organization_id": 1,
                    "list_of_speakers_default_structure_level_time": 30,
                },
                "user/7": {
                    "username": "test_username1",
                    "meeting_user_ids": [7],
                },
                "meeting_user/7": {
                    "meeting_id": 111,
                    "user_id": 7,
                    "speaker_ids": [890],
                    "structure_level_ids": [5],
                },
                "list_of_speakers/23": {
                    "speaker_ids": [890],
                    "structure_level_list_of_speakers_ids": [9],
                },
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 111,
                    "structure_level_list_of_speakers_id": 9,
                    "begin_time": 123456789,
                },
                "structure_level_list_of_speakers/9": {
                    "structure_level_id": 5,
                    "list_of_speakers_id": 23,
                    "speaker_ids": [890],
                    "initial_time": 30,
                    "remaining_time": 30,
                    "current_start_time": 123456789,
                    "meeting_id": 111,
                },
                "structure_level/5": {
                    "name": "Lvl",
                    "structure_level_list_of_speakers_ids": [9],
                    "default_time": 30,
                    "meeting_user_ids": [7],
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("speaker/890")
        sllos = self.assert_model_exists(
            "structure_level_list_of_speakers/9",
            {
                "current_start_time": None,
                "structure_level_id": 5,
                "list_of_speakers_id": 23,
                "speaker_ids": [],
                "initial_time": 30,
                "meeting_id": 111,
            },
        )
        assert sllos["remaining_time"] < 30

    def test_with_paused_structure_level_speaker(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "speaker_ids": [890],
                    "is_active_in_organization_id": 1,
                    "list_of_speakers_default_structure_level_time": 30,
                },
                "user/7": {
                    "username": "test_username1",
                    "meeting_user_ids": [7],
                },
                "meeting_user/7": {
                    "meeting_id": 111,
                    "user_id": 7,
                    "speaker_ids": [890],
                    "structure_level_ids": [5],
                },
                "list_of_speakers/23": {
                    "speaker_ids": [890],
                    "structure_level_list_of_speakers_ids": [9],
                },
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 111,
                    "structure_level_list_of_speakers_id": 9,
                    "begin_time": 123456789,
                    "pause_time": 123456800,
                },
                "structure_level_list_of_speakers/9": {
                    "structure_level_id": 5,
                    "list_of_speakers_id": 23,
                    "speaker_ids": [890],
                    "initial_time": 30,
                    "remaining_time": 18,
                    "meeting_id": 111,
                },
                "structure_level/5": {
                    "name": "Lvl",
                    "structure_level_list_of_speakers_ids": [9],
                    "default_time": 30,
                    "meeting_user_ids": [7],
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("speaker/890")
        sllos = self.assert_model_exists(
            "structure_level_list_of_speakers/9",
            {
                "current_start_time": None,
                "structure_level_id": 5,
                "list_of_speakers_id": 23,
                "speaker_ids": [],
                "initial_time": 30,
                "meeting_id": 111,
            },
        )
        assert sllos["remaining_time"] == 18

    def add_coupled_countdown(self) -> int:
        """Returns the current date that was used to set the countdown_time"""
        now = floor(time())
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_couple_countdown": True,
                    "list_of_speakers_countdown_id": 75,
                },
                "projector_countdown/75": {
                    "running": True,
                    "default_time": 200,
                    "countdown_time": now + 100,
                    "meeting_id": 1,
                },
                "speaker/890": {
                    "begin_time": now + 100,
                },
            }
        )
        return now

    def test_delete_update_countdown(self) -> None:
        self.set_models(self.permission_test_models)
        self.add_coupled_countdown()
        response = self.request("speaker.delete", {"id": 890})
        self.assert_status_code(response, 200)
        countdown = self.get_model("projector_countdown/75")
        assert countdown.get("running") is False
        self.assertAlmostEqual(countdown["countdown_time"], 100, delta=200)

    def test_delete_dont_update_countdown(self) -> None:
        self.set_models(self.permission_test_models)
        self.set_models(
            {
                "meeting/1": {
                    "speaker_ids": [890, 891],
                    "meeting_user_ids": [7, 8],
                },
                "user/8": {
                    "username": "test_username2",
                    "meeting_user_ids": [8],
                    "is_active": True,
                    "default_password": DEFAULT_PASSWORD,
                    "password": self.auth.hash(DEFAULT_PASSWORD),
                },
                "meeting_user/8": {"meeting_id": 1, "user_id": 8, "speaker_ids": [891]},
                "list_of_speakers/23": {"speaker_ids": [890, 891]},
                "speaker/891": {
                    "meeting_user_id": 8,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                },
            }
        )
        now = self.add_coupled_countdown()
        response = self.request("speaker.delete", {"id": 891})
        self.assert_status_code(response, 200)
        countdown = self.assert_model_exists(
            "projector_countdown/75",
            {
                "running": True,
                "default_time": 200,
                "meeting_id": 1,
            },
        )
        self.assertAlmostEqual(countdown["countdown_time"], now, delta=200)
