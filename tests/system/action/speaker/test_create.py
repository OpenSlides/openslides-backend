from time import time
from typing import Any

from openslides_backend.action.actions.speaker.speech_state import SpeechState
from openslides_backend.action.mixins.delegation_based_restriction_mixin import (
    DelegationBasedRestriction,
)
from openslides_backend.permissions.base_classes import Permission
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase

DEFAULT_PASSWORD = "password"


class SpeakerCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "name": "name_asdewqasd",
                "is_active_in_organization_id": 1,
                "meeting_user_ids": [7],
            },
            "user/7": {
                "username": "test_username1",
                "meeting_ids": [1],
                "is_active": True,
                "default_password": DEFAULT_PASSWORD,
                "password": self.auth.hash(DEFAULT_PASSWORD),
                "meeting_user_ids": [17],
            },
            "meeting_user/17": {"meeting_id": 1, "user_id": 7},
            "list_of_speakers/23": {"speaker_ids": [], "meeting_id": 1},
        }

    def test_create(self) -> None:
        self.set_models(self.test_models)
        response = self.request(
            "speaker.create", {"meeting_user_id": 17, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/1",
            {
                "meeting_user_id": 17,
                "list_of_speakers_id": 23,
                "weight": 1,
            },
        )
        self.assert_model_exists("list_of_speakers/23", {"speaker_ids": [1]})
        self.assert_model_exists("user/7", {"meeting_user_ids": [17]})

    def test_create_in_closed_los(self) -> None:
        self.test_models["list_of_speakers/23"]["closed"] = True
        self.set_models(self.test_models)

        response = self.request(
            "speaker.create", {"meeting_user_id": 17, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/1",
            {
                "meeting_user_id": 17,
                "list_of_speakers_id": 23,
                "weight": 1,
            },
        )
        self.assert_model_exists("list_of_speakers/23", {"speaker_ids": [1]})
        self.assert_model_exists("user/7", {"meeting_user_ids": [17]})
        self.assert_model_exists("meeting_user/17", {"speaker_ids": [1]})

    def test_create_oneself_in_closed_los(self) -> None:
        self.test_models["list_of_speakers/23"]["closed"] = True
        self.test_models["group/1"] = {
            "meeting_id": 1,
            "name": "g1",
            "permissions": [
                Permissions.ListOfSpeakers.CAN_BE_SPEAKER,
            ],
        }
        self.set_models(self.test_models)
        self.set_user_groups(7, [1])
        self.user_id = 7
        self.login(self.user_id)
        response = self.request(
            "speaker.create", {"meeting_user_id": 17, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 400)
        self.assertIn("The list of speakers is closed.", response.json["message"])

    def test_create_oneself_in_closed_los_with_los_CAN_MANAGE(self) -> None:
        self.test_models["list_of_speakers/23"]["closed"] = True
        self.test_models["group/1"] = {
            "meeting_id": 1,
            "name": "g1",
            "permissions": [
                Permissions.ListOfSpeakers.CAN_MANAGE,
                Permissions.ListOfSpeakers.CAN_BE_SPEAKER,
            ],
        }
        self.set_models(self.test_models)
        self.set_user_groups(7, [1])
        self.user_id = 7
        self.login(self.user_id)
        response = self.request(
            "speaker.create", {"meeting_user_id": 17, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 200)

    def test_create_point_of_order_in_closed_los(self) -> None:
        self.test_models["list_of_speakers/23"]["closed"] = True
        self.test_models["meeting/1"][
            "list_of_speakers_enable_point_of_order_speakers"
        ] = True
        self.test_models["meeting/1"]["group_ids"] = [3]
        self.test_models["group/3"] = {"name": "permission group", "meeting_id": 1}
        self.test_models["point_of_order_category/1"] = {"rank": 1, "meeting_id": 1}
        self.set_models(self.test_models)
        self.login(7)
        self.set_user_groups(7, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_BE_SPEAKER])

        response = self.request(
            "speaker.create",
            {"meeting_user_id": 17, "list_of_speakers_id": 23, "point_of_order": True},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/1",
            {
                "meeting_user_id": 17,
                "list_of_speakers_id": 23,
                "weight": 1,
                "point_of_order": True,
            },
        )
        self.assert_model_exists("list_of_speakers/23", {"speaker_ids": [1]})
        self.assert_model_exists(
            "meeting_user/17", {"user_id": 7, "meeting_id": 1, "speaker_ids": [1]}
        )
        self.assert_model_exists("user/7", {"meeting_user_ids": [17]})

    def test_create_point_of_order_in_closed_los_with_submission_restricted(
        self,
    ) -> None:
        self.test_models["list_of_speakers/23"]["closed"] = True
        self.test_models["meeting/1"][
            "list_of_speakers_enable_point_of_order_speakers"
        ] = True
        self.test_models["meeting/1"][
            "list_of_speakers_closing_disables_point_of_order"
        ] = True
        self.test_models["meeting/1"]["group_ids"] = [3]
        self.test_models["group/3"] = {"name": "permission group", "meeting_id": 1}
        self.test_models["point_of_order_category/1"] = {"rank": 1, "meeting_id": 1}
        self.set_models(self.test_models)
        self.login(7)
        self.set_user_groups(7, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_BE_SPEAKER])
        response = self.request(
            "speaker.create",
            {"meeting_user_id": 17, "list_of_speakers_id": 23, "point_of_order": True},
        )
        self.assert_status_code(response, 400)
        self.assertIn("The list of speakers is closed.", response.json["message"])

    def test_create_empty_data(self) -> None:
        response = self.request("speaker.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['list_of_speakers_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request("speaker.create", {"wrong_field": "text_AefohteiF8"})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['list_of_speakers_id'] properties",
            response.json["message"],
        )

    def setup_multiple_speakers(self, allow: bool = False) -> None:
        self.test_models["list_of_speakers/23"]["speaker_ids"] = [42]
        self.test_models["meeting/1"][
            "list_of_speakers_allow_multiple_speakers"
        ] = allow
        self.set_models(
            {
                **self.test_models,
                "speaker/42": {
                    "meeting_user_id": 17,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                },
            }
        )

    def test_create_already_exists(self) -> None:
        self.setup_multiple_speakers()
        response = self.request(
            "speaker.create", {"meeting_user_id": 17, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 7 is already on the list of speakers.",
            response.json["message"],
        )
        list_of_speakers = self.get_model("list_of_speakers/23")
        assert list_of_speakers.get("speaker_ids") == [42]

    def test_create_multiple_speakers(self) -> None:
        self.setup_multiple_speakers(True)
        response = self.request(
            "speaker.create", {"meeting_user_id": 17, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/43",
            {"meeting_user_id": 17, "list_of_speakers_id": 23},
        )

    def test_create_add_2_speakers_in_1_action(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "list_of_speakers/23": {"meeting_id": 1},
                "user/2": {"username": "another user"},
                "meeting_user/11": {"meeting_id": 1, "user_id": 1},
                "meeting_user/12": {"meeting_id": 1, "user_id": 2},
            }
        )
        response = self.request_multi(
            "speaker.create",
            [
                {"meeting_user_id": 11, "list_of_speakers_id": 23},
                {"meeting_user_id": 12, "list_of_speakers_id": 23},
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain less than or equal to 1 items",
            response.json["message"],
        )

    def test_create_add_2_speakers_in_2_actions(self) -> None:
        self.set_models(
            {
                "meeting/7844": {
                    "is_active_in_organization_id": 1,
                },
                "user/7": {"meeting_ids": [7844]},
                "user/8": {"meeting_ids": [7844]},
                "user/9": {"meeting_ids": [7844]},
                "meeting_user/17": {
                    "meeting_id": 7844,
                    "user_id": 7,
                    "speaker_ids": [1],
                },
                "meeting_user/18": {"meeting_id": 7844, "user_id": 8},
                "meeting_user/19": {"meeting_id": 7844, "user_id": 9},
                "speaker/1": {
                    "meeting_user_id": 17,
                    "list_of_speakers_id": 23,
                    "weight": 10000,
                },
                "list_of_speakers/23": {"speaker_ids": [1], "meeting_id": 7844},
            }
        )
        response = self.request_json(
            [
                {
                    "action": "speaker.create",
                    "data": [
                        {"meeting_user_id": 18, "list_of_speakers_id": 23},
                    ],
                },
                {
                    "action": "speaker.create",
                    "data": [
                        {"meeting_user_id": 19, "list_of_speakers_id": 23},
                    ],
                },
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Action speaker.create may not appear twice in one request.",
            response.json["message"],
        )

    def test_create_user_present(self) -> None:
        self.set_models(
            {
                "meeting/7844": {
                    "name": "name_asdewqasd",
                    "list_of_speakers_present_users_only": True,
                    "is_active_in_organization_id": 1,
                },
                "user/9": {
                    "username": "user9",
                    "meeting_user_ids": [19],
                    "is_present_in_meeting_ids": [7844],
                    "meeting_ids": [7844],
                },
                "meeting_user/19": {
                    "meeting_id": 7844,
                    "user_id": 9,
                    "speaker_ids": [3],
                },
                "list_of_speakers/23": {"speaker_ids": [], "meeting_id": 7844},
            }
        )
        response = self.request(
            "speaker.create",
            {
                "meeting_user_id": 19,
                "list_of_speakers_id": 23,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("speaker/1")

    def test_create_user_not_present(self) -> None:
        self.set_models(
            {
                "meeting/7844": {
                    "name": "name_asdewqasd",
                    "list_of_speakers_present_users_only": True,
                    "is_active_in_organization_id": 1,
                },
                "user/9": {
                    "username": "user9",
                    "meeting_user_ids": [19],
                    "meeting_ids": [7844],
                },
                "meeting_user/19": {
                    "meeting_id": 7844,
                    "user_id": 9,
                    "speaker_ids": [3],
                },
                "list_of_speakers/23": {"speaker_ids": [], "meeting_id": 7844},
            }
        )
        response = self.request(
            "speaker.create",
            {
                "meeting_user_id": 19,
                "list_of_speakers_id": 23,
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("speaker/1")
        self.assertIn(
            "Only present users can be on the lists of speakers.",
            response.json["message"],
        )

    def test_create_standard_speaker_in_only_talker_list(self) -> None:
        self.set_models(
            {
                "meeting/7844": {
                    "name": "name_asdewqasd",
                    "is_active_in_organization_id": 1,
                },
                "user/1": {"meeting_ids": [7844]},
                "meeting_user/11": {
                    "meeting_id": 7844,
                    "user_id": 1,
                    "speaker_ids": [1],
                },
                "user/7": {"username": "talking", "meeting_ids": [7844]},
                "speaker/1": {
                    "meeting_user_id": 17,
                    "list_of_speakers_id": 23,
                    "begin_time": 100000,
                    "weight": 5,
                    "meeting_id": 7844,
                },
                "list_of_speakers/23": {"speaker_ids": [1], "meeting_id": 7844},
            }
        )
        response = self.request(
            "speaker.create", {"meeting_user_id": 11, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/2",
            {"meeting_user_id": 11, "weight": 1},
        )
        self.assert_model_exists("list_of_speakers/23", {"speaker_ids": [1, 2]})

    def test_create_standard_speaker_at_the_end_of_filled_list(self) -> None:
        self.set_models(
            {
                "meeting/7844": {
                    "name": "name_asdewqasd",
                    "is_active_in_organization_id": 1,
                },
                "user/7": {
                    "username": "talking",
                    "meeting_ids": [7844],
                    "meeting_user_ids": [17],
                },
                "user/8": {
                    "username": "waiting",
                    "meeting_ids": [7844],
                    "meeting_user_ids": [18],
                },
                "user/1": {
                    "meeting_user_ids": [11],
                    "meeting_ids": [7844],
                },
                "meeting_user/11": {
                    "meeting_id": 7844,
                    "user_id": 1,
                    "speaker_ids": [3],
                },
                "meeting_user/17": {
                    "meeting_id": 7844,
                    "user_id": 7,
                    "speaker_ids": [1],
                },
                "meeting_user/18": {
                    "meeting_id": 7844,
                    "user_id": 8,
                    "speaker_ids": [2],
                },
                "speaker/1": {
                    "meeting_user_id": 17,
                    "list_of_speakers_id": 23,
                    "begin_time": 100000,
                    "weight": 5,
                    "meeting_id": 7844,
                },
                "speaker/2": {
                    "meeting_user_id": 18,
                    "list_of_speakers_id": 23,
                    "weight": 1,
                    "meeting_id": 7844,
                },
                "speaker/3": {
                    "meeting_user_id": 11,
                    "list_of_speakers_id": 23,
                    "point_of_order": True,
                    "weight": 2,
                    "meeting_id": 7844,
                },
                "list_of_speakers/23": {"speaker_ids": [1, 2, 3], "meeting_id": 7844},
            }
        )
        response = self.request(
            "speaker.create", {"meeting_user_id": 11, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/3",
            {"meeting_user_id": 11, "point_of_order": True, "weight": 2},
        )
        self.assert_model_exists(
            "speaker/4",
            {"meeting_user_id": 11, "point_of_order": None, "weight": 3},
        )
        self.assert_model_exists("list_of_speakers/23", {"speaker_ids": [1, 2, 3, 4]})

    def test_create_not_in_meeting(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "meeting/2": {"is_active_in_organization_id": 1},
                "user/7": {"meeting_ids": [1]},
                "meeting_user/17": {"meeting_id": 1, "user_id": 7},
                "list_of_speakers/23": {"speaker_ids": [], "meeting_id": 2},
            }
        )
        response = self.request(
            "speaker.create", {"meeting_user_id": 17, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 400)

    def test_create_note_and_not_point_of_order(self) -> None:
        self.set_models(self.test_models)
        response = self.request(
            "speaker.create",
            {"meeting_user_id": 17, "list_of_speakers_id": 23, "note": "blablabla"},
        )
        self.assert_status_code(response, 400)
        assert (
            "Not allowed to set note/category if not point of order."
            in response.json["message"]
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "speaker.create",
            {"meeting_user_id": 17, "list_of_speakers_id": 23},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "speaker.create",
            {"meeting_user_id": 17, "list_of_speakers_id": 23},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.test_models,
            "speaker.create",
            {"meeting_user_id": 17, "list_of_speakers_id": 23},
        )

    def test_create_permissions_selfadd(self) -> None:
        self.create_meeting()
        self.user_id = 7
        self.set_models(self.test_models)
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_BE_SPEAKER])
        response = self.request(
            "speaker.create", {"meeting_user_id": 17, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 200)

    def base_state_speech_test(
        self,
        status_code: int,
        speech_state: str,
        self_contribution: bool = True,
        pro_contra: bool = True,
        assert_message: str = "",
    ) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_MANAGE])
        self.test_models["meeting/1"][
            "list_of_speakers_enable_pro_contra_speech"
        ] = pro_contra
        self.test_models["meeting/1"][
            "list_of_speakers_can_set_contribution_self"
        ] = self_contribution
        self.set_models(self.test_models)
        response = self.request(
            "speaker.create",
            {
                "meeting_user_id": 17,
                "list_of_speakers_id": 23,
                "speech_state": speech_state,
            },
        )
        self.assert_status_code(response, status_code)
        assert assert_message in response.json["message"]

    def test_create_pro_contra(self) -> None:
        self.base_state_speech_test(200, SpeechState.PRO, False, True)

    def test_create_contradiction(self) -> None:
        self.base_state_speech_test(200, SpeechState.CONTRIBUTION)

    def test_create_contradiction_2(self) -> None:
        self.base_state_speech_test(200, SpeechState.CONTRIBUTION, False)

    def test_create_not_allowed_pro_contra(self) -> None:
        self.base_state_speech_test(
            400, SpeechState.PRO, False, False, "Pro/Contra is not enabled."
        )

    def test_create_not_allowed_contribution(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_BE_SPEAKER])
        self.set_models(self.test_models)
        self.set_models({"meeting_user/1": {"meeting_id": 1, "user_id": self.user_id}})
        response = self.request(
            "speaker.create",
            {
                "meeting_user_id": 1,
                "list_of_speakers_id": 23,
                "speech_state": SpeechState.CONTRIBUTION,
            },
        )
        self.assert_status_code(response, 400)
        assert "Self contribution is not allowed" in response.json["message"]

    def test_create_missing_category_id(self) -> None:
        self.test_models["meeting/1"][
            "list_of_speakers_enable_point_of_order_categories"
        ] = True
        self.test_models["meeting/1"][
            "list_of_speakers_enable_point_of_order_speakers"
        ] = True
        self.test_models["group/3"] = {"name": "permission group", "meeting_id": 1}
        self.test_models["meeting/1"]["group_ids"] = [3]
        self.set_models(self.test_models)
        self.login(7)
        self.set_user_groups(7, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_BE_SPEAKER])
        response = self.request(
            "speaker.create",
            {"meeting_user_id": 17, "list_of_speakers_id": 23, "point_of_order": True},
        )
        self.assert_status_code(response, 400)
        assert (
            "Point of order category is enabled, but category id is missing."
            in response.json["message"]
        )

    def test_create_categories_not_enabled(self) -> None:
        self.test_models["meeting/1"][
            "list_of_speakers_enable_point_of_order_speakers"
        ] = True
        self.test_models["meeting/1"]["point_of_order_category_ids"] = [1]
        self.test_models["meeting/1"]["group_ids"] = [3]
        self.test_models["group/3"] = {"name": "permission group", "meeting_id": 1}
        self.test_models["point_of_order_category/1"] = {"rank": 1, "meeting_id": 1}
        self.set_models(self.test_models)
        self.login(7)
        self.set_user_groups(7, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_BE_SPEAKER])
        response = self.request(
            "speaker.create",
            {
                "meeting_user_id": 17,
                "list_of_speakers_id": 23,
                "point_of_order": True,
                "point_of_order_category_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Point of order categories are not enabled for this meeting."
            in response.json["message"]
        )

    def test_create_category_without_point_of_order(self) -> None:
        self.test_models["meeting/1"][
            "list_of_speakers_enable_point_of_order_categories"
        ] = True
        self.test_models["meeting/1"][
            "list_of_speakers_enable_point_of_order_speakers"
        ] = True
        self.test_models["meeting/1"]["point_of_order_category_ids"] = [1]
        self.test_models["meeting/1"]["group_ids"] = [3]
        self.test_models["group/3"] = {"name": "permission group", "meeting_id": 1}
        self.test_models["point_of_order_category/1"] = {"rank": 1, "meeting_id": 1}
        self.set_models(self.test_models)
        self.login(7)
        self.set_user_groups(7, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_BE_SPEAKER])
        response = self.request(
            "speaker.create",
            {
                "meeting_user_id": 17,
                "list_of_speakers_id": 23,
                "point_of_order_category_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Not allowed to set note/category if not point of order."
            in response.json["message"]
        )

    def test_create_category_weights_with_ranks(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "name_asdewqasd",
                    "is_active_in_organization_id": 1,
                    "list_of_speakers_enable_point_of_order_categories": True,
                    "list_of_speakers_enable_point_of_order_speakers": True,
                    "point_of_order_category_ids": [2, 3, 5],
                    "meeting_user_ids": [11],
                },
                "user/1": {
                    "meeting_ids": [1],
                },
                "meeting_user/11": {"user_id": 1, "meeting_id": 1},
                "point_of_order_category/2": {
                    "rank": 2,
                    "meeting_id": 1,
                },
                "point_of_order_category/3": {
                    "rank": 3,
                    "meeting_id": 1,
                },
                "point_of_order_category/5": {
                    "rank": 5,
                    "meeting_id": 1,
                },
                "speaker/1": {
                    "weight": 1,
                    "point_of_order": True,
                    "point_of_order_category_id": 2,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                },
                "speaker/2": {
                    "weight": 2,
                    "point_of_order": True,
                    "point_of_order_category_id": 3,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                },
                "speaker/3": {
                    "weight": 3,
                    "point_of_order": False,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                },
                "speaker/4": {
                    "weight": 4,
                    "point_of_order": True,
                    "point_of_order_category_id": 5,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                },
                "speaker/5": {
                    "begin_time": 100000,
                    "weight": 2,
                    "point_of_order": True,
                    "point_of_order_category_id": 5,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                },
                "list_of_speakers/23": {
                    "speaker_ids": [1, 2, 3, 4, 5],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "speaker.create",
            {
                "meeting_user_id": 11,
                "list_of_speakers_id": 23,
                "point_of_order": True,
                "point_of_order_category_id": 3,
                "note": "this is my note",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("speaker/1", {"weight": 1})
        self.assert_model_exists("speaker/2", {"weight": 2})
        self.assert_model_exists(
            "speaker/6",
            {
                "weight": 3,
                "point_of_order_category_id": 3,
                "point_of_order": True,
                "note": "this is my note",
            },
        )
        self.assert_model_exists("speaker/3", {"weight": 4})
        self.assert_model_exists("speaker/4", {"weight": 5})
        self.assert_model_exists("speaker/5", {"weight": 2})

    def test_create_category_key_error_problem(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "name_asdewqasd",
                    "is_active_in_organization_id": 1,
                    "list_of_speakers_enable_point_of_order_categories": True,
                    "list_of_speakers_enable_point_of_order_speakers": True,
                    "point_of_order_category_ids": [2, 3, 5],
                },
                "user/1": {
                    "meeting_ids": [1],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 1,
                },
                "point_of_order_category/2": {
                    "rank": 2,
                    "meeting_id": 1,
                },
                "point_of_order_category/3": {
                    "rank": 3,
                    "meeting_id": 1,
                },
                "point_of_order_category/5": {
                    "rank": 5,
                    "meeting_id": 1,
                },
                "speaker/1": {
                    "weight": 1,
                    "point_of_order": True,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                },
                "list_of_speakers/23": {"speaker_ids": [1], "meeting_id": 1},
            }
        )
        response = self.request(
            "speaker.create",
            {
                "meeting_user_id": 11,
                "list_of_speakers_id": 23,
                "point_of_order": True,
                "point_of_order_category_id": 3,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/2",
            {
                "meeting_user_id": 11,
                "list_of_speakers_id": 23,
                "point_of_order": True,
                "point_of_order_category_id": 3,
                "weight": 1,
            },
        )
        self.assert_model_exists("speaker/1", {"weight": 2})

    def test_create_with_existing_structure_level(self) -> None:
        self.test_models["meeting/1"]["structure_level_ids"] = [1]
        self.test_models["meeting/1"]["structure_level_list_of_speakers_ids"] = [42]
        self.test_models["list_of_speakers/23"][
            "structure_level_list_of_speakers_ids"
        ] = [42]
        self.test_models["structure_level/1"] = {
            "meeting_id": 1,
            "structure_level_list_of_speakers_ids": [42],
        }
        self.test_models["structure_level_list_of_speakers/42"] = {
            "meeting_id": 1,
            "structure_level_id": 1,
            "list_of_speakers_id": 23,
        }
        self.set_models(self.test_models)
        response = self.request(
            "speaker.create",
            {"meeting_user_id": 17, "list_of_speakers_id": 23, "structure_level_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/1",
            {
                "structure_level_list_of_speakers_id": 42,
            },
        )
        self.assert_model_exists(
            "structure_level_list_of_speakers/42", {"speaker_ids": [1]}
        )

    def test_create_with_new_structure_level(self) -> None:
        self.test_models["meeting/1"]["structure_level_ids"] = [1]
        self.test_models["meeting/1"][
            "list_of_speakers_default_structure_level_time"
        ] = 100
        self.test_models["structure_level/1"] = {
            "meeting_id": 1,
        }
        self.set_models(self.test_models)
        response = self.request(
            "speaker.create",
            {"meeting_user_id": 17, "list_of_speakers_id": 23, "structure_level_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/1",
            {
                "structure_level_list_of_speakers_id": 1,
            },
        )
        self.assert_model_exists(
            "structure_level_list_of_speakers/1",
            {
                "meeting_id": 1,
                "list_of_speakers_id": 23,
                "structure_level_id": 1,
                "speaker_ids": [1],
                "initial_time": 100,
                "remaining_time": 100,
            },
        )

    def test_create_intervention(self) -> None:
        self.test_models["meeting/1"]["list_of_speakers_intervention_time"] = 100
        self.set_models(self.test_models)
        response = self.request(
            "speaker.create",
            {
                "meeting_user_id": 17,
                "list_of_speakers_id": 23,
                "speech_state": SpeechState.INTERVENTION,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/1",
            {
                "meeting_user_id": 17,
                "list_of_speakers_id": 23,
                "weight": 1,
                "speech_state": SpeechState.INTERVENTION,
            },
        )

    def test_create_interposed_question(self) -> None:
        self.test_models["meeting/1"][
            "list_of_speakers_enable_interposed_question"
        ] = True
        self.set_models(self.test_models)
        response = self.request(
            "speaker.create",
            {
                "meeting_user_id": 17,
                "list_of_speakers_id": 23,
                "speech_state": SpeechState.INTERPOSED_QUESTION,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/1",
            {
                "meeting_user_id": 17,
                "list_of_speakers_id": 23,
                "weight": 1,
                "speech_state": SpeechState.INTERPOSED_QUESTION,
            },
        )

    def test_create_interposed_question_without_meeting_user_id(self) -> None:
        self.test_models["meeting/1"][
            "list_of_speakers_enable_interposed_question"
        ] = True
        self.set_models(self.test_models)
        response = self.request(
            "speaker.create",
            {
                "list_of_speakers_id": 23,
                "speech_state": SpeechState.INTERPOSED_QUESTION,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/1",
            {
                "list_of_speakers_id": 23,
                "weight": 1,
                "speech_state": SpeechState.INTERPOSED_QUESTION,
            },
        )

    def test_create_other_state_without_meeting_user_id(self) -> None:
        self.test_models["meeting/1"]["list_of_speakers_intervention_time"] = 100
        self.set_models(self.test_models)
        for state in (
            SpeechState.PRO,
            SpeechState.CONTRA,
            SpeechState.CONTRIBUTION,
            SpeechState.INTERVENTION,
        ):
            response = self.request(
                "speaker.create", {"list_of_speakers_id": 23, "speech_state": state}
            )
            self.assert_status_code(response, 400)

    def test_create_interposed_question_with_multiple_speakers(self) -> None:
        self.test_models["meeting/1"][
            "list_of_speakers_enable_interposed_question"
        ] = True
        self.set_models(
            {
                **self.test_models,
                "speaker/1": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                    "weight": 1,
                    "begin_time": round(time()),
                },
                "speaker/2": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                    "weight": 2,
                    "speech_state": SpeechState.INTERPOSED_QUESTION,
                },
                "speaker/3": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                    "weight": 3,
                    "point_of_order": True,
                },
                "speaker/4": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                    "weight": 4,
                },
            }
        )
        response = self.request(
            "speaker.create",
            {
                "list_of_speakers_id": 23,
                "speech_state": SpeechState.INTERPOSED_QUESTION,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/1",
            {
                "weight": 1,
            },
        )
        self.assert_model_exists(
            "speaker/2",
            {
                "weight": 1,
            },
        )
        self.assert_model_exists(
            "speaker/5",
            {
                "weight": 2,
            },
        )
        self.assert_model_exists(
            "speaker/3",
            {
                "weight": 3,
            },
        )
        self.assert_model_exists(
            "speaker/4",
            {
                "weight": 4,
            },
        )

    def test_create_with_point_of_order_and_speech_state(self) -> None:
        self.set_models(self.test_models)
        response = self.request(
            "speaker.create",
            {
                "meeting_user_id": 17,
                "list_of_speakers_id": 23,
                "point_of_order": True,
                "speech_state": SpeechState.CONTRIBUTION,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Speaker can't be point of order and another speech state at the same time."
        )

    def create_delegator_test_data(
        self,
        is_delegator: bool = False,
        perm: Permission = Permissions.ListOfSpeakers.CAN_BE_SPEAKER,
        delegator_setting: DelegationBasedRestriction = "users_forbid_delegator_in_list_of_speakers",
        disable_delegations: bool = False,
    ) -> None:
        self.create_meeting(1)
        self.set_models(self.test_models)
        self.set_models(
            {
                "user/1": {"meeting_user_ids": [1]},
                "meeting_user/1": {"user_id": 1, "meeting_id": 1},
                "meeting/1": {
                    "meeting_user_ids": [1, 17],
                    **(
                        {}
                        if disable_delegations
                        else {"users_enable_vote_delegations": True}
                    ),
                    delegator_setting: True,
                },
            }
        )
        if is_delegator:
            self.create_user("delegatee", [1])
            self.set_models(
                {
                    "meeting_user/1": {"vote_delegated_to_id": 2},
                    "meeting_user/2": {"vote_delegations_from_ids": [1]},
                }
            )
        self.set_organization_management_level(None)
        self.set_group_permissions(1, [perm])
        self.set_user_groups(1, [1])

    def test_delegator_setting_with_no_delegation(self) -> None:
        self.create_delegator_test_data()
        response = self.request(
            "speaker.create", {"meeting_user_id": 1, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 200)

    def test_delegator_setting_with_no_delegation_set_others(self) -> None:
        self.create_delegator_test_data()
        response = self.request(
            "speaker.create", {"meeting_user_id": 17, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action speaker.create. Missing Permission: list_of_speakers.can_manage"
        )

    def test_delegator_setting_with_delegation(self) -> None:
        self.create_delegator_test_data(is_delegator=True)
        response = self.request(
            "speaker.create", {"meeting_user_id": 1, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action speaker.create. Missing Permission: list_of_speakers.can_manage"
        )

    def test_delegator_setting_with_motion_manager_delegation(
        self,
    ) -> None:
        self.create_delegator_test_data(
            is_delegator=True, perm=Permissions.ListOfSpeakers.CAN_MANAGE
        )
        response = self.request(
            "speaker.create", {"meeting_user_id": 1, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 200)

    def test_delegator_setting_with_no_delegation_set_others_delegations_turned_off(
        self,
    ) -> None:
        self.create_delegator_test_data(disable_delegations=True)
        response = self.request(
            "speaker.create", {"meeting_user_id": 17, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action speaker.create. Missing Permission: list_of_speakers.can_manage"
        )

    def test_delegator_setting_with_delegation_delegations_turned_off(self) -> None:
        self.create_delegator_test_data(is_delegator=True, disable_delegations=True)
        response = self.request(
            "speaker.create", {"meeting_user_id": 1, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 200)

    def test_delegator_setting_with_motion_manager_delegation_delegations_turned_off(
        self,
    ) -> None:
        self.create_delegator_test_data(
            is_delegator=True,
            perm=Permissions.ListOfSpeakers.CAN_BE_SPEAKER,
            disable_delegations=True,
        )
        response = self.request(
            "speaker.create", {"meeting_user_id": 1, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 200)

    def test_with_irrelevant_delegator_setting(self) -> None:
        self.create_delegator_test_data(
            is_delegator=True, delegator_setting="users_forbid_delegator_as_submitter"
        )
        response = self.request(
            "speaker.create", {"meeting_user_id": 1, "list_of_speakers_id": 23}
        )
        self.assert_status_code(response, 200)
