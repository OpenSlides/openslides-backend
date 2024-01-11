from math import ceil, floor
from time import time
from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class SpeakerEndSpeachTester(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.models: Dict[str, Dict[str, Any]] = {
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
        self.set_models(self.models)

    def test_correct(self) -> None:
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        self.assertIsNotNone(model.get("end_time"))

    def test_wrong_id(self) -> None:
        response = self.request("speaker.end_speech", {"id": 889})
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertIsNone(model.get("end_time"))
        self.assertIn("Model 'speaker/889' does not exist.", response.json["message"])

    def test_end_time_set(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "end_time": 200000,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertEqual(model.get("begin_time"), 10000)
        self.assertEqual(model.get("end_time"), 200000)
        self.assertIn(
            "Speaker 890 is not speaking at the moment.", response.json["message"]
        )

    def test_no_begin_time(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "begin_time": None,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertIsNone(model.get("begin_time"))
        self.assertIsNone(model.get("end_time"))
        self.assertIn(
            "Speaker 890 is not speaking at the moment.", response.json["message"]
        )

    def test_reset_countdown(self) -> None:
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 200)
        countdown = self.get_model("projector_countdown/11")
        self.assertFalse(countdown.get("running"))
        self.assertEqual(countdown.get("countdown_time"), 60)

    def test_correct_on_closed_los(self) -> None:
        self.set_models(
            {
                "list_of_speakers/23": {
                    "closed": True,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        self.assertIsNotNone(model.get("end_time"))

    def test_with_structure_level(self) -> None:
        start = floor(time())
        self.set_models(
            {
                "meeting/1": {
                    "structure_level_ids": [1],
                    "structure_level_list_of_speakers_ids": [2],
                },
                "structure_level/1": {
                    "meeting_id": 1,
                    "structure_level_list_of_speakers_ids": [2],
                },
                "structure_level_list_of_speakers/2": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                    "structure_level_id": 1,
                    "speaker_ids": [890],
                    "remaining_time": 500,
                    "current_start_time": start - 100,
                },
                "list_of_speakers/23": {"structure_level_list_of_speakers_ids": [2]},
                "speaker/890": {
                    "begin_time": start - 100,
                    "structure_level_list_of_speakers_id": 2,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 200)
        speaker = self.get_model("speaker/890")
        model = self.get_model("structure_level_list_of_speakers/2")
        self.assertEqual(
            model["remaining_time"], 500 - (speaker["end_time"] - speaker["begin_time"])
        )
        self.assertIsNone(model.get("current_start_time"))

    def test_paused_speaker(self) -> None:
        start = floor(time())
        self.set_models(
            {
                "meeting/1": {
                    "structure_level_ids": [1],
                    "structure_level_list_of_speakers_ids": [2],
                },
                "structure_level/1": {
                    "meeting_id": 1,
                    "structure_level_list_of_speakers_ids": [2],
                },
                "structure_level_list_of_speakers/2": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                    "structure_level_id": 1,
                    "speaker_ids": [890],
                    "remaining_time": 500,
                    "current_start_time": start - 100,
                },
                "list_of_speakers/23": {"structure_level_list_of_speakers_ids": [2]},
                "speaker/890": {
                    "begin_time": start - 100,
                    "pause_time": start - 50,
                    "total_pause": 20,
                    "structure_level_list_of_speakers_id": 2,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        end = ceil(time())
        delta = end - start
        self.assert_status_code(response, 200)
        speaker = self.assert_model_exists(
            "speaker/890",
            {
                "begin_time": start - 100,
                "pause_time": None,
            },
        )
        self.assertAlmostEqual(speaker["total_pause"], 70, delta=delta)
        self.assertAlmostEqual(speaker["end_time"], end, delta=delta)
        model = self.get_model("structure_level_list_of_speakers/2")
        self.assertEqual(
            model["remaining_time"],
            500
            - (speaker["end_time"] - speaker["begin_time"] - speaker["total_pause"]),
        )
        self.assertIsNone(model.get("current_start_time"))

    def test_paused_speaker_without_total_pause(self) -> None:
        start = floor(time())
        self.set_models(
            {
                "speaker/890": {
                    "begin_time": start - 100,
                    "pause_time": start - 50,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        end = ceil(time())
        delta = end - start
        self.assert_status_code(response, 200)
        speaker = self.assert_model_exists(
            "speaker/890",
            {
                "begin_time": start - 100,
                "pause_time": None,
            },
        )
        self.assertAlmostEqual(speaker["total_pause"], 50, delta=delta)
        self.assertAlmostEqual(speaker["end_time"], end, delta=delta)

    def test_end_speech_no_permissions(self) -> None:
        self.base_permission_test(self.models, "speaker.end_speech", {"id": 890})

    def test_end_speech_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "speaker.end_speech",
            {"id": 890},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )
