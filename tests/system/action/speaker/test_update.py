from time import time
from typing import Any

from openslides_backend.action.actions.speaker.speech_state import SpeechState
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class SpeakerUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "list_of_speakers_enable_pro_contra_speech": True,
                "is_active_in_organization_id": 1,
                "meeting_user_ids": [7],
                "speaker_ids": [890],
            },
            "user/7": {"username": "test_username1", "meeting_user_ids": [7]},
            "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
            "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 1},
            "speaker/890": {
                "meeting_user_id": 7,
                "list_of_speakers_id": 23,
                "meeting_id": 1,
            },
        }
        self.set_models(self.models)

    def test_update_correct(self) -> None:
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == SpeechState.PRO

    def test_update_same_speech_state(self) -> None:
        self.models["speaker/890"]["speech_state"] = SpeechState.PRO
        self.set_models(self.models)
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == SpeechState.PRO

    def test_update_contribution_ok(self) -> None:
        self.set_models(
            {"meeting/1": {"list_of_speakers_can_set_contribution_self": True}}
        )
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.CONTRIBUTION}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == SpeechState.CONTRIBUTION

    def test_update_contribution_fail(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"organization_management_level": None},
                "meeting_user/7": {"user_id": 1},
            }
        )
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_SEE])

        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.CONTRIBUTION}
        )
        self.assert_status_code(response, 400)
        assert "Self contribution is not allowed" in response.json["message"]

    def test_update_pro_contra_ok(self) -> None:
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == SpeechState.PRO

    def test_update_pro_contra_fail(self) -> None:
        self.set_models(
            {"meeting/1": {"list_of_speakers_enable_pro_contra_speech": False}}
        )
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 400)

    def test_update_unset_contribution_ok(self) -> None:
        self.set_models(
            {
                "meeting/1": {"list_of_speakers_can_set_contribution_self": True},
                "speaker/890": {"speech_state": SpeechState.CONTRIBUTION},
            }
        )
        response = self.request("speaker.update", {"id": 890, "speech_state": None})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") is None

    def test_update_unset_contribution_fail(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"organization_management_level": None},
                "meeting_user/7": {"user_id": 1},
                "speaker/890": {"speech_state": SpeechState.CONTRIBUTION},
            }
        )
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_SEE])
        response = self.request("speaker.update", {"id": 890, "speech_state": None})
        self.assert_status_code(response, 400)
        assert "Self contribution is not allowed" in response.json["message"]

    def test_update_unset_pro_contra_ok(self) -> None:
        self.set_models({"speaker/890": {"speech_state": SpeechState.CONTRA}})
        response = self.request("speaker.update", {"id": 890, "speech_state": None})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") is None

    def test_update_unset_pro_contra_fail(self) -> None:
        self.set_models(
            {
                "meeting/1": {"list_of_speakers_enable_pro_contra_speech": False},
                "speaker/890": {"speech_state": SpeechState.CONTRA},
            }
        )
        response = self.request("speaker.update", {"id": 890, "speech_state": None})
        self.assert_status_code(response, 400)
        assert "Pro/Contra is not enabled" in response.json["message"]

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "speaker/890": {"speech_state": SpeechState.CONTRA},
            }
        )
        response = self.request(
            "speaker.update", {"id": 889, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == SpeechState.CONTRA

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "speaker.update",
            {"id": 890, "speech_state": SpeechState.PRO},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "speaker.update",
            {"id": 890, "speech_state": SpeechState.PRO},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_update_check_request_user_is_user_not_can_see(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"organization_management_level": None},
                "meeting_user/7": {"user_id": 1},
            }
        )
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 403)

    def test_update_check_request_user_is_user_permission_can_see(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"organization_management_level": None},
                "meeting_user/7": {"user_id": 1},
            }
        )
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_SEE])
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 200)

    def test_update_check_request_user_is_user_permission_can_be_speaker(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"organization_management_level": None},
                "meeting_user/7": {"user_id": 1},
            }
        )
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_BE_SPEAKER])
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 200)

    def test_update_can_see_but_not_request_user_eq_user(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"organization_management_level": None},
            }
        )
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_SEE])
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 403)

    def test_update_correct_on_closed_los(self) -> None:
        self.set_models(
            {
                "list_of_speakers/23": {
                    "closed": True,
                },
            }
        )
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("speaker/890", {"speech_state": SpeechState.PRO})

    def test_update_with_removed_user(self) -> None:
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == SpeechState.PRO

    def test_update_with_deleted_user(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "meeting_user_id": None,
                },
            }
        )
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == SpeechState.PRO

    def test_update_change_from_intervention(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "speech_state": SpeechState.INTERVENTION,
                },
            }
        )
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 200)

    def test_update_change_from_interposed_question(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "speech_state": SpeechState.INTERPOSED_QUESTION,
                },
            }
        )
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 400)

    def test_update_set_intervention(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_intervention_time": 60,
                }
            }
        )
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.INTERVENTION}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/890", {"speech_state": SpeechState.INTERVENTION}
        )

    def test_update_set_interposed_question(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_enable_interposed_question": True,
                }
            }
        )
        response = self.request(
            "speaker.update",
            {"id": 890, "speech_state": SpeechState.INTERPOSED_QUESTION},
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("speaker/890", {"speech_state": None})

    def test_update_meeting_user(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "speech_state": SpeechState.INTERPOSED_QUESTION,
                    "meeting_user_id": None,
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "meeting_user_id": 7})
        self.assert_status_code(response, 200)
        self.assert_model_exists("speaker/890", {"meeting_user_id": 7})

    def test_update_meeting_user_and_structure_level_on_past_speaker(self) -> None:
        now = round(time())
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_default_structure_level_time": 60,
                    "structure_level_ids": [2],
                },
                "structure_level/2": {
                    "meeting_id": 1,
                },
                "speaker/890": {
                    "speech_state": SpeechState.INTERPOSED_QUESTION,
                    "meeting_user_id": None,
                    "begin_time": now - 100,
                    "end_time": now - 50,
                },
            }
        )
        response = self.request(
            "speaker.update", {"id": 890, "meeting_user_id": 7, "structure_level_id": 2}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/890",
            {"meeting_user_id": 7, "structure_level_list_of_speakers_id": 1},
        )

    def test_update_meeting_user_and_structure_level_on_past_speaker_without_default_time(
        self,
    ) -> None:
        now = round(time())
        self.set_models(
            {
                "meeting/1": {
                    "structure_level_ids": [2],
                },
                "structure_level/2": {
                    "meeting_id": 1,
                },
                "speaker/890": {
                    "speech_state": SpeechState.INTERPOSED_QUESTION,
                    "meeting_user_id": None,
                    "begin_time": now - 100,
                    "end_time": now - 50,
                },
            }
        )
        response = self.request(
            "speaker.update", {"id": 890, "meeting_user_id": 7, "structure_level_id": 2}
        )
        self.assert_status_code(response, 400)
        assert "Structure level countdowns are deactivated" in response.json["message"]

    def test_update_meeting_user_wrong_state(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "speech_state": SpeechState.INTERVENTION,
                    "meeting_user_id": None,
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "meeting_user_id": 7})
        self.assert_status_code(response, 400)
        self.assert_model_exists("speaker/890", {"meeting_user_id": None})

    def test_update_meeting_user_already_set(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "speech_state": SpeechState.INTERPOSED_QUESTION,
                },
                "meeting_user/8": {
                    "user_id": 1,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "meeting_user_id": 8})
        self.assert_status_code(response, 400)
        self.assert_model_exists("speaker/890", {"meeting_user_id": 7})

    def test_update_meeting_user_set_none(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "speech_state": SpeechState.INTERPOSED_QUESTION,
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "meeting_user_id": None})
        self.assert_status_code(response, 400)
        self.assert_model_exists("speaker/890", {"meeting_user_id": 7})

    def test_update_structure_level_existing(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "structure_level_ids": [1],
                    "structure_level_list_of_speakers_ids": [42],
                },
                "list_of_speakers/23": {
                    "structure_level_list_of_speakers_ids": [42],
                },
                "structure_level/1": {
                    "meeting_id": 1,
                    "structure_level_list_of_speakers_ids": [42],
                },
                "structure_level_list_of_speakers/42": {
                    "meeting_id": 1,
                    "structure_level_id": 1,
                    "list_of_speakers_id": 23,
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "structure_level_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/890", {"structure_level_list_of_speakers_id": 42}
        )

    def test_update_structure_level_new(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_default_structure_level_time": 60,
                    "structure_level_ids": [2],
                },
                "structure_level/2": {
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "structure_level_id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/890", {"structure_level_list_of_speakers_id": 1}
        )
        self.assert_model_exists(
            "structure_level_list_of_speakers/1",
            {"speaker_ids": [890], "structure_level_id": 2},
        )

    def test_update_structure_level_already_speaking(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "structure_level_ids": [1],
                    "structure_level_list_of_speakers_ids": [42],
                },
                "list_of_speakers/23": {
                    "structure_level_list_of_speakers_ids": [42],
                },
                "structure_level/1": {
                    "meeting_id": 1,
                    "structure_level_list_of_speakers_ids": [42],
                },
                "structure_level_list_of_speakers/42": {
                    "meeting_id": 1,
                    "structure_level_id": 1,
                    "list_of_speakers_id": 23,
                },
                "speaker/890": {
                    "begin_time": round(time()),
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "structure_level_id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual(
            response.json["message"],
            "You can only update the structure level on a waiting speaker.",
        )

    def test_update_structure_level_none(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "structure_level_ids": [1],
                    "structure_level_list_of_speakers_ids": [42],
                },
                "list_of_speakers/23": {
                    "structure_level_list_of_speakers_ids": [42],
                },
                "structure_level/1": {
                    "meeting_id": 1,
                    "structure_level_list_of_speakers_ids": [42],
                },
                "structure_level_list_of_speakers/42": {
                    "meeting_id": 1,
                    "structure_level_id": 1,
                    "list_of_speakers_id": 23,
                    "speaker_ids": [890],
                },
                "speaker/890": {
                    "structure_level_list_of_speakers_id": 42,
                },
            }
        )
        response = self.request(
            "speaker.update", {"id": 890, "structure_level_id": None}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/890", {"structure_level_list_of_speakers_id": None}
        )
        self.assert_model_exists(
            "structure_level_list_of_speakers/42", {"speaker_ids": []}
        )

    def test_update_set_point_of_order_forbidden(self) -> None:
        response = self.request("speaker.update", {"id": 890, "point_of_order": True})
        self.assert_status_code(response, 400)
        self.assertEqual(
            response.json["message"],
            "Point of order speakers are not enabled for this meeting.",
        )
        self.assert_model_exists("speaker/890", {"point_of_order": None})

    def test_update_set_point_of_order_self(self) -> None:
        self.set_models(
            {
                "meeting/1": {"list_of_speakers_enable_point_of_order_speakers": True},
                "meeting_user/7": {"user_id": 1},
            }
        )
        response = self.request("speaker.update", {"id": 890, "point_of_order": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists("speaker/890", {"point_of_order": True})

    def test_update_set_point_of_order_other_forbidden(self) -> None:
        self.set_models(
            {"meeting/1": {"list_of_speakers_enable_point_of_order_speakers": True}}
        )
        response = self.request("speaker.update", {"id": 890, "point_of_order": True})
        self.assert_status_code(response, 400)
        self.assertEqual(
            response.json["message"],
            "The requesting user 1 is not the user 7 the point-of-order is filed for.",
        )
        self.assert_model_exists("speaker/890", {"point_of_order": None})

    def test_update_set_point_of_order_other_allowed(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_enable_point_of_order_speakers": True,
                    "list_of_speakers_can_create_point_of_order_for_others": True,
                }
            }
        )
        response = self.request("speaker.update", {"id": 890, "point_of_order": True})
        self.assert_status_code(response, 200)
        self.assert_model_exists("speaker/890", {"point_of_order": True})

    def test_update_poo_fields_without_poo(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_enable_point_of_order_speakers": True,
                    "list_of_speakers_enable_point_of_order_categories": True,
                },
                "point_of_order_category/1": {
                    "meeting_id": 1,
                },
            }
        )
        for field, value in {"note": "test", "point_of_order_category_id": 1}.items():
            response = self.request("speaker.update", {"id": 890, field: value})
            self.assert_status_code(response, 400)
            self.assertEqual(
                response.json["message"],
                "Not allowed to set note/category if not point of order.",
            )
            self.assert_model_exists("speaker/890", {field: None})

    def test_update_missing_poo_category(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_enable_point_of_order_speakers": True,
                    "list_of_speakers_enable_point_of_order_categories": True,
                    "list_of_speakers_can_create_point_of_order_for_others": True,
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "point_of_order": True})
        self.assert_status_code(response, 400)
        self.assertEqual(
            response.json["message"],
            "Point of order category is enabled, but category id is missing.",
        )
        self.assert_model_exists("speaker/890", {"point_of_order": None})

    def test_update_forbidden_poo_category(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_enable_point_of_order_speakers": True,
                    "list_of_speakers_can_create_point_of_order_for_others": True,
                },
                "point_of_order_category/1": {
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "speaker.update",
            {"id": 890, "point_of_order": True, "point_of_order_category_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            response.json["message"],
            "Point of order categories are not enabled for this meeting.",
        )
        self.assert_model_exists("speaker/890", {"point_of_order": None})

    def test_update_with_point_of_order_and_speech_state(self) -> None:
        response = self.request(
            "speaker.update",
            {
                "id": 890,
                "point_of_order": True,
                "speech_state": SpeechState.CONTRIBUTION,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Speaker can't be point of order and another speech state at the same time."
        )

    def test_update_with_point_of_order_and_speech_state_2(self) -> None:
        self.set_models({"speaker/890": {"speech_state": SpeechState.PRO}})
        response = self.request("speaker.update", {"id": 890, "point_of_order": True})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Speaker can't be point of order and another speech state at the same time."
        )

    def test_update_with_point_of_order_and_speech_state_3(self) -> None:
        self.set_models({"speaker/890": {"point_of_order": True}})
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.CONTRIBUTION}
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Speaker can't be point of order and another speech state at the same time."
        )

    def test_update_running_intervention_with_other_state(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "speech_state": SpeechState.INTERVENTION,
                    "begin_time": 1234,
                }
            }
        )
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.CONTRIBUTION}
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "You can not change the speech_state of a started intervention."
        )

    def test_update_non_running_intervention_with_other_state(self) -> None:
        self.set_models({"speaker/890": {"speech_state": SpeechState.INTERVENTION}})
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.CONTRIBUTION}
        )
        self.assert_status_code(response, 200)

    def test_update_running_intervention_with_point_of_order(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "speech_state": SpeechState.INTERVENTION,
                    "begin_time": 1234,
                }
            }
        )
        response = self.request("speaker.update", {"id": 890, "point_of_order": True})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "You can not change the speech_state of a started intervention."
        )

    def test_update_running_speaker_with_speech_state(self) -> None:
        self.set_models({"speaker/890": {"begin_time": 1234}})
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 200)

    def test_update_running_point_of_order_with_speech_state(self) -> None:
        self.set_models({"speaker/890": {"point_of_order": True, "begin_time": 1234}})
        response = self.request(
            "speaker.update",
            {"id": 890, "speech_state": SpeechState.CONTRA, "point_of_order": False},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/890", {"speech_state": SpeechState.CONTRA, "point_of_order": False}
        )

    def test_update_running_non_intervention_speech_state_with_point_of_order(
        self,
    ) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_enable_point_of_order_speakers": True,
                    "list_of_speakers_can_create_point_of_order_for_others": True,
                },
                "speaker/890": {"speech_state": SpeechState.CONTRA, "begin_time": 1234},
            }
        )
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": None, "point_of_order": True}
        )
        self.assert_status_code(response, 200)
        speaker = self.assert_model_exists("speaker/890", {"point_of_order": True})
        assert "speech_state" not in speaker

    def create_list_of_speakers_with_structure_level(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_enable_point_of_order_speakers": True,
                    "list_of_speakers_can_create_point_of_order_for_others": True,
                    "structure_level_ids": [1],
                    "structure_level_list_of_speakers_ids": [1],
                    "list_of_speakers_intervention_time": 1,
                },
                "structure_level/1": {
                    "name": "Level",
                    "meeting_id": 1,
                    "meeting_user_ids": [7],
                },
                "structure_level_list_of_speakers/1": {
                    "list_of_speakers_id": 23,
                    "speaker_ids": [890],
                    "meeting_id": 1,
                },
                "speaker/890": {
                    "begin_time": 1234,
                    "structure_level_list_of_speakers_id": 1,
                },
            }
        )

    def test_update_running_structure_level_speaker_with_point_of_order(self) -> None:
        self.create_list_of_speakers_with_structure_level()
        response = self.request("speaker.update", {"id": 890, "point_of_order": True})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "You can not change a started speaker to point_of_order if there is a structure_level."
        )

    def test_update_running_structure_level_speaker_with_pro(self) -> None:
        self.create_list_of_speakers_with_structure_level()
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.PRO}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("speaker/890", {"speech_state": SpeechState.PRO})

    def test_update_running_structure_level_speaker_with_contra(self) -> None:
        self.create_list_of_speakers_with_structure_level()
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.CONTRA}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("speaker/890", {"speech_state": SpeechState.CONTRA})

    def test_update_running_structure_level_speaker_with_contribution(self) -> None:
        self.create_list_of_speakers_with_structure_level()
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.CONTRIBUTION}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/890", {"speech_state": SpeechState.CONTRIBUTION}
        )

    def test_update_running_structure_level_speaker_with_interposed_question(
        self,
    ) -> None:
        self.create_list_of_speakers_with_structure_level()
        response = self.request(
            "speaker.update",
            {"id": 890, "speech_state": SpeechState.INTERPOSED_QUESTION},
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "You cannot set the speech state to interposed_question."
        )

    def test_update_running_structure_level_speaker_with_intervention(self) -> None:
        self.create_list_of_speakers_with_structure_level()
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": SpeechState.INTERVENTION}
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "You can not change a started speaker to intervention if there is a structure_level."
        )

    def test_update_with_internal_fields(self) -> None:
        self.set_models(
            {
                "meeting/1": {"structure_level_list_of_speakers_ids": [90]},
                "list_of_speakers/23": {"structure_level_list_of_speakers_ids": [90]},
                "structure_level_list_of_speakers/90": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                },
            }
        )
        response = self.request(
            "speaker.update",
            {"id": 890, "weight": 4, "structure_level_list_of_speakers_id": 90},
            internal=True,
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/890", {"weight": 4, "structure_level_list_of_speakers_id": 90}
        )

    def test_update_with_internal_fields_error(self) -> None:
        self.set_models(
            {
                "meeting/1": {"structure_level_list_of_speakers_ids": [90]},
                "list_of_speakers/23": {"structure_level_list_of_speakers_ids": [90]},
                "structure_level_list_of_speakers/90": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                },
            }
        )
        response = self.request(
            "speaker.update",
            {"id": 890, "weight": 4, "structure_level_list_of_speakers_id": 90},
            internal=False,
        )
        self.assert_status_code(response, 400)
        message: str = response.json["message"]
        assert message.startswith("data must not contain {")
        assert message.endswith("} properties")
        for field in [
            "'structure_level_list_of_speakers_id'",
            "'weight'",
        ]:
            self.assertIn(field, message)
