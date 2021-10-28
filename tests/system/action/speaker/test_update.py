from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class SpeakerUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model: Dict[str, Dict[str, Any]] = {
            "meeting/1": {
                "list_of_speakers_enable_pro_contra_speech": True,
                "is_active_in_organization_id": 1,
            },
            "user/7": {"username": "test_username1"},
            "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 1},
            "speaker/890": {"user_id": 7, "list_of_speakers_id": 23, "meeting_id": 1},
        }

    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_enable_pro_contra_speech": True,
                    "is_active_in_organization_id": 1,
                },
                "user/7": {"username": "test_username1"},
                "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 1},
                "speaker/890": {
                    "user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == "pro"

    def test_update_same_speech_state(self) -> None:
        self.permission_test_model["speaker/890"]["speech_state"] = "pro"
        self.set_models(self.permission_test_model)
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == "pro"

    def test_update_contribution_ok(self) -> None:
        self.permission_test_model["meeting/1"][
            "list_of_speakers_can_set_contribution_self"
        ] = True
        self.set_models(self.permission_test_model)
        response = self.request(
            "speaker.update", {"id": 890, "speech_state": "contribution"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == "contribution"

    def test_update_contribution_fail(self) -> None:
        self.create_meeting()
        self.permission_test_model["speaker/890"]["user_id"] = 1
        self.set_models(self.permission_test_model)
        self.set_models({"user/1": {"organization_management_level": None}})
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_SEE])

        response = self.request(
            "speaker.update", {"id": 890, "speech_state": "contribution"}
        )
        self.assert_status_code(response, 400)
        assert "Self contribution is not allowed" in response.json["message"]

    def test_update_pro_contra_ok(self) -> None:
        self.set_models(self.permission_test_model)
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == "pro"

    def test_update_pro_contra_fail(self) -> None:
        self.permission_test_model["meeting/1"][
            "list_of_speakers_enable_pro_contra_speech"
        ] = False
        self.set_models(self.permission_test_model)
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 400)

    def test_update_unset_contribution_ok(self) -> None:
        self.permission_test_model["speaker/890"]["speech_state"] = "contribution"
        self.permission_test_model["meeting/1"][
            "list_of_speakers_can_set_contribution_self"
        ] = True
        self.set_models(self.permission_test_model)
        response = self.request("speaker.update", {"id": 890, "speech_state": None})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") is None

    def test_update_unset_contribution_fail(self) -> None:
        self.permission_test_model["speaker/890"]["speech_state"] = "contribution"
        self.permission_test_model["meeting/1"][
            "list_of_speakers_can_set_contribution_self"
        ] = False
        self.create_meeting()
        self.permission_test_model["speaker/890"]["user_id"] = 1
        self.set_models(self.permission_test_model)
        self.set_models({"user/1": {"organization_management_level": None}})
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_SEE])
        response = self.request("speaker.update", {"id": 890, "speech_state": None})
        self.assert_status_code(response, 400)
        assert "Self contribution is not allowed" in response.json["message"]

    def test_update_unset_pro_contra_ok(self) -> None:
        self.permission_test_model["speaker/890"]["speech_state"] = "contra"
        self.set_models(self.permission_test_model)
        response = self.request("speaker.update", {"id": 890, "speech_state": None})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") is None

    def test_update_unset_pro_contra_fail(self) -> None:
        self.permission_test_model["speaker/890"]["speech_state"] = "contra"
        self.permission_test_model["meeting/1"][
            "list_of_speakers_enable_pro_contra_speech"
        ] = False
        self.set_models(self.permission_test_model)
        response = self.request("speaker.update", {"id": 890, "speech_state": None})
        self.assert_status_code(response, 400)
        assert "Pro/Contra is not enabled" in response.json["message"]

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "user/7": {"username": "test_username1"},
                "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 1},
                "speaker/890": {
                    "user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                    "speech_state": "contra",
                },
            }
        )
        response = self.request("speaker.update", {"id": 889, "speech_state": "pro"})
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        assert model.get("speech_state") == "contra"

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "speaker.update",
            {"id": 890, "speech_state": "pro"},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "speaker.update",
            {"id": 890, "speech_state": "pro"},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_update_check_request_user_is_user_not_can_see(self) -> None:
        self.create_meeting()
        self.set_models(self.permission_test_model)
        self.set_models(
            {
                "user/1": {"organization_management_level": None},
                "speaker/890": {"user_id": 1},
            }
        )
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 403)

    def test_update_check_request_user_is_user_permission(self) -> None:
        self.create_meeting()
        self.set_models(self.permission_test_model)
        self.set_models(
            {
                "user/1": {"organization_management_level": None},
                "speaker/890": {"user_id": 1},
            }
        )
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.ListOfSpeakers.CAN_SEE])
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 200)

    def test_update_can_see_but_not_request_user_eq_user(self) -> None:
        self.create_meeting()
        self.set_models(self.permission_test_model)
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
                "meeting/1": {
                    "list_of_speakers_enable_pro_contra_speech": True,
                    "is_active_in_organization_id": 1,
                },
                "user/7": {"username": "test_username1"},
                "list_of_speakers/23": {
                    "speaker_ids": [890],
                    "meeting_id": 1,
                    "closed": True,
                },
                "speaker/890": {
                    "user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("speaker.update", {"id": 890, "speech_state": "pro"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("speaker/890", {"speech_state": "pro"})
