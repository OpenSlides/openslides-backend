from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class SpeakerUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.models: Dict[str, Dict[str, Any]] = {
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
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == "pro"

    def test_update_same_speech_state(self) -> None:
        self.models["speaker/890"]["speech_state"] = "pro"
        self.set_models(self.models)
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == "pro"

    def test_update_contribution_ok(self) -> None:
        self.set_models(
            {"meeting/1": {"list_of_speakers_can_set_contribution_self": True}}
        )
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": "contribution"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == "contribution"

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
            "speaker.update", {"id": 890, "speech_state": "contribution"}
        )
        self.assert_status_code(response, 400)
        assert "Self contribution is not allowed" in response.json["message"]

    def test_update_pro_contra_ok(self) -> None:
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == "pro"

    def test_update_pro_contra_fail(self) -> None:
        self.set_models(
            {"meeting/1": {"list_of_speakers_enable_pro_contra_speech": False}}
        )
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 400)

    def test_update_unset_contribution_ok(self) -> None:
        self.set_models(
            {
                "meeting/1": {"list_of_speakers_can_set_contribution_self": True},
                "speaker/890": {"speech_state": "contribution"},
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
                "speaker/890": {"speech_state": "contribution"},
            }
        )
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_SEE])
        response = self.request("speaker.update", {"id": 890, "speech_state": None})
        self.assert_status_code(response, 400)
        assert "Self contribution is not allowed" in response.json["message"]

    def test_update_unset_pro_contra_ok(self) -> None:
        self.set_models({"speaker/890": {"speech_state": "contra"}})
        response = self.request("speaker.update", {"id": 890, "speech_state": None})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") is None

    def test_update_unset_pro_contra_fail(self) -> None:
        self.set_models(
            {
                "meeting/1": {"list_of_speakers_enable_pro_contra_speech": False},
                "speaker/890": {"speech_state": "contra"},
            }
        )
        response = self.request("speaker.update", {"id": 890, "speech_state": None})
        self.assert_status_code(response, 400)
        assert "Pro/Contra is not enabled" in response.json["message"]

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "speaker/890": {"speech_state": "contra"},
            }
        )
        response = self.request("speaker.update", {"id": 889, "speech_state": "pro"})
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == "contra"

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "speaker.update",
            {"id": 890, "speech_state": "pro"},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "speaker.update",
            {"id": 890, "speech_state": "pro"},
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
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
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
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
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
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
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
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 403)

    def test_update_correct_on_closed_los(self) -> None:
        self.set_models(
            {
                "list_of_speakers/23": {
                    "closed": True,
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("speaker/890", {"speech_state": "pro"})

    def test_update_with_removed_user(self) -> None:
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == "pro"

    def test_update_with_deleted_user(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "meeting_user_id": None,
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == "pro"

    def test_update_change_state_forbidden(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_intervention_time": 60,
                    "list_of_speakers_enable_interposed_question": True,
                }
            }
        )
        for state in ("interposed_question", "intervention"):
            self.set_models(
                {
                    "speaker/890": {
                        "speech_state": state,
                    },
                }
            )
            response = self.request(
                "speaker.update", {"id": 890, "speech_state": "pro"}
            )
            self.assert_status_code(response, 400)
            self.set_models(
                {
                    "speaker/890": {
                        "speech_state": "pro",
                    },
                }
            )
            response = self.request(
                "speaker.update", {"id": 890, "speech_state": state}
            )
            self.assert_status_code(response, 400)

    def test_update_meeting_user(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "speech_state": "interposed_question",
                    "meeting_user_id": None,
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "meeting_user_id": 7})
        self.assert_status_code(response, 200)
        self.assert_model_exists("speaker/890", {"meeting_user_id": 7})

    def test_update_meeting_user_wrong_state(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "speech_state": "intervention",
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
                    "speech_state": "interposed_question",
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
                    "speech_state": "interposed_question",
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "meeting_user_id": None})
        self.assert_status_code(response, 400)
        self.assert_model_exists("speaker/890", {"meeting_user_id": 7})
