from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class SpeakerEndSpeachTester(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "list_of_speakers_couple_countdown": True,
                "list_of_speakers_countdown_id": 11,
                "is_active_in_organization_id": 1,
                "meeting_user_ids": [7],
            },
            "projector_countdown/11": {
                "running": True,
                "default_time": 60,
                "countdown_time": 31.0,
                "meeting_id": 1,
            },
            "user/7": {"username": "test_username1", "meeting_user_ids": [7]},
            "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
            "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 1},
            "speaker/890": {
                "meeting_user_id": 7,
                "list_of_speakers_id": 23,
                "begin_time": 10000,
                "meeting_id": 1,
            },
        }

    def test_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_couple_countdown": True,
                    "list_of_speakers_countdown_id": 11,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [7],
                },
                "projector_countdown/11": {
                    "running": True,
                    "default_time": 60,
                    "countdown_time": 31.0,
                    "meeting_id": 1,
                },
                "user/7": {
                    "username": "test_username1",
                    "meeting_user_ids": [7],
                },
                "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
                "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 1},
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "begin_time": 10000,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        self.assertTrue(model.get("end_time") is not None)

    def test_wrong_id(self) -> None:
        self.set_models(
            {
                "user/7": {"username": "test_username1", "meeting_user_ids": [7]},
                "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
                "list_of_speakers/23": {"speaker_ids": [890]},
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "begin_time": 10000,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 889})
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertTrue(model.get("end_time") is None)
        self.assertTrue(
            "Model 'speaker/889' does not exist." in response.json["message"]
        )

    def test_existing_speaker(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "user/7": {"username": "test_username1"},
                "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
                "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 1},
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "begin_time": 100000,
                    "end_time": 200000,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertEqual(model.get("begin_time"), 100000)
        self.assertEqual(model.get("end_time"), 200000)
        self.assertTrue(
            "Speaker 890 is not speaking at the moment." in response.json["message"]
        )

    def test_existing_speaker_2(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "user/7": {"username": "test_username1"},
                "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
                "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 1},
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertTrue(model.get("begin_time") is None)
        self.assertTrue(model.get("end_time") is None)
        self.assertTrue(
            "Speaker 890 is not speaking at the moment." in response.json["message"]
        )

    def test_reset_countdown(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_couple_countdown": True,
                    "list_of_speakers_countdown_id": 11,
                    "is_active_in_organization_id": 1,
                },
                "projector_countdown/11": {
                    "running": True,
                    "default_time": 60,
                    "countdown_time": 31.0,
                    "meeting_id": 1,
                },
                "user/7": {"username": "test_username1"},
                "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
                "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 1},
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "begin_time": 10000,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 200)
        countdown = self.get_model("projector_countdown/11")
        assert countdown.get("running") is False
        assert countdown.get("countdown_time") == 60

    def test_end_speech_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models, "speaker.end_speech", {"id": 890}
        )

    def test_end_speech_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "speaker.end_speech",
            {"id": 890},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_correct_on_closed_los(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "user/7": {"username": "test_username1"},
                "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
                "list_of_speakers/23": {
                    "speaker_ids": [890],
                    "meeting_id": 1,
                    "closed": True,
                },
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "begin_time": 10000,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        self.assertIsNotNone(model.get("end_time"))
