from datetime import datetime, timedelta
from math import floor
from typing import Any
from zoneinfo import ZoneInfo

from openslides_backend.action.actions.speaker.speech_state import SpeechState
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class SpeakerEndSpeachTester(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "list_of_speakers_couple_countdown": True,
                "list_of_speakers_countdown_id": 11,
            },
            "projector_countdown/11": {
                "title": "weisichnich",
                "running": True,
                "default_time": 60,
                "countdown_time": 31.0,
                "meeting_id": 1,
            },
            "user/7": {"username": "test_username1"},
            "meeting_user/7": {"meeting_id": 1, "user_id": 7},
            "group/1": {"meeting_user_ids": [7]},
            "topic/1337": {
                "title": "introduction leet gathering",
                "meeting_id": 1,
            },
            "agenda_item/1": {"content_object_id": "topic/1337", "meeting_id": 1},
            "list_of_speakers/23": {
                "content_object_id": "topic/1337",
                "meeting_id": 1,
            },
            "speaker/890": {
                "meeting_user_id": 7,
                "list_of_speakers_id": 23,
                "begin_time": datetime.fromtimestamp(10000),
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
        end_time = datetime.fromtimestamp(200000, tz=ZoneInfo("UTC"))
        self.set_models(
            {
                "speaker/890": {
                    "end_time": end_time,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertEqual(
            model.get("begin_time"),
            datetime.fromtimestamp(10000, tz=ZoneInfo("UTC")),
        )
        self.assertEqual(model.get("end_time"), end_time)
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
        start = datetime.now()
        begin_time = start - timedelta(100)
        self.set_models(
            {
                "structure_level/1": {
                    "name": "auf los",
                    "meeting_id": 1,
                },
                "structure_level_list_of_speakers/2": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                    "structure_level_id": 1,
                    "initial_time": 600,
                    "remaining_time": 500,
                    "current_start_time": begin_time,
                },
                "speaker/890": {
                    "begin_time": begin_time,
                    "structure_level_list_of_speakers_id": 2,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 200)
        speaker = self.get_model("speaker/890")
        model = self.get_model("structure_level_list_of_speakers/2")
        self.assertEqual(
            model["remaining_time"],
            500 - floor((speaker["end_time"] - speaker["begin_time"]).total_seconds()),
        )
        self.assertIsNone(model.get("current_start_time"))

    def test_with_structure_level_and_unpause_time(self) -> None:
        start = datetime.now()
        self.set_models(
            {
                "structure_level/1": {
                    "name": "BB maniacs",
                    "meeting_id": 1,
                },
                "structure_level_list_of_speakers/2": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                    "structure_level_id": 1,
                    "initial_time": 600,
                    "remaining_time": 500,
                    "current_start_time": start - timedelta(seconds=100),
                },
                "speaker/890": {
                    "begin_time": start - timedelta(seconds=200),
                    "unpause_time": start - timedelta(seconds=100),
                    "structure_level_list_of_speakers_id": 2,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 200)
        speaker = self.get_model("speaker/890")
        model = self.get_model("structure_level_list_of_speakers/2")
        self.assertEqual(
            model["remaining_time"],
            500
            - floor((speaker["end_time"] - speaker["unpause_time"]).total_seconds()),
        )
        self.assertIsNone(model.get("current_start_time"))

    def test_paused_speaker(self) -> None:
        start = datetime.now(tz=ZoneInfo("UTC"))
        self.set_models(
            {
                "structure_level/1": {
                    "name": "level 1",
                    "meeting_id": 1,
                },
                "structure_level_list_of_speakers/2": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                    "structure_level_id": 1,
                    "initial_time": 600,
                    "remaining_time": 500,
                },
                "speaker/890": {
                    "begin_time": start - timedelta(seconds=100),
                    "pause_time": start - timedelta(seconds=50),
                    "total_pause": 20,
                    "structure_level_list_of_speakers_id": 2,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        end = datetime.now(tz=ZoneInfo("UTC"))
        delta = (end - start).total_seconds()
        self.assert_status_code(response, 200)
        speaker = self.assert_model_exists(
            "speaker/890",
            {
                "begin_time": start - timedelta(seconds=100),
                "pause_time": None,
            },
        )
        self.assertAlmostEqual(speaker["total_pause"], 70, delta=delta)
        self.assertAlmostEqual(
            speaker["end_time"].timestamp(), end.timestamp(), delta=delta
        )
        model = self.get_model("structure_level_list_of_speakers/2")
        self.assertEqual(model["remaining_time"], 500)

    def test_paused_speaker_without_total_pause(self) -> None:
        start = datetime.now(tz=ZoneInfo("UTC"))
        self.set_models(
            {
                "speaker/890": {
                    "begin_time": start - timedelta(seconds=100),
                    "pause_time": start - timedelta(seconds=50),
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        end = datetime.now(tz=ZoneInfo("UTC"))
        delta = (end - start).total_seconds()
        self.assert_status_code(response, 200)
        speaker = self.assert_model_exists(
            "speaker/890",
            {
                "begin_time": start - timedelta(seconds=100),
                "pause_time": None,
            },
        )
        self.assertAlmostEqual(speaker["total_pause"], 50, delta=delta)
        self.assertAlmostEqual(
            speaker["end_time"].timestamp(), end.timestamp(), delta=delta
        )

    def with_structure_level_and_speech_state(self, state: SpeechState) -> None:
        start = datetime.now()
        self.set_models(
            {
                "structure_level/1": {
                    "name": "los",
                    "meeting_id": 1,
                },
                "structure_level_list_of_speakers/2": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                    "structure_level_id": 1,
                    "initial_time": 600,
                    "remaining_time": 500,
                },
                "speaker/890": {
                    "begin_time": start - timedelta(100),
                    "structure_level_list_of_speakers_id": 2,
                    "speech_state": state,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/2", {"remaining_time": 500}
        )

    def test_interposed_question(self) -> None:
        self.with_structure_level_and_speech_state(SpeechState.INTERPOSED_QUESTION)

    def test_intervention(self) -> None:
        self.with_structure_level_and_speech_state(SpeechState.INTERVENTION)

    def test_with_structure_level_and_point_of_order(self) -> None:
        start = datetime.now()
        self.set_models(
            {
                "structure_level/1": {
                    "name": "geht's los",
                    "meeting_id": 1,
                },
                "structure_level_list_of_speakers/2": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                    "structure_level_id": 1,
                    "initial_time": 600,
                    "remaining_time": 500,
                },
                "speaker/890": {
                    "begin_time": start - timedelta(100),
                    "structure_level_list_of_speakers_id": 2,
                    "point_of_order": True,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/2", {"remaining_time": 500}
        )

    def test_end_started_child_interposed_question(self) -> None:
        self.set_models(
            {
                "list_of_speakers/23": {"meeting_id": 1},
                "speaker/890": {
                    "pause_time": datetime.fromtimestamp(11000),
                },
                "speaker/891": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "begin_time": datetime.fromtimestamp(10000),
                    "speech_state": SpeechState.INTERPOSED_QUESTION,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 200)
        speaker = self.get_model("speaker/891")
        self.assertIsNotNone(speaker.get("end_time"))
        self.assert_model_exists("speaker/890", {"end_time": speaker["end_time"]})

    def test_end_waiting_child_interposed_question(self) -> None:
        self.set_models(
            {
                "speaker/891": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "speech_state": SpeechState.INTERPOSED_QUESTION,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("speaker.end_speech", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("speaker/891")

    def test_end_speech_no_permissions(self) -> None:
        self.base_permission_test(self.models, "speaker.end_speech", {"id": 890})

    def test_end_speech_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "speaker.end_speech",
            {"id": 890},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_end_speech_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.models,
            "speaker.end_speech",
            {"id": 890},
        )
