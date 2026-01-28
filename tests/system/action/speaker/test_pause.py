from datetime import datetime, timedelta
from math import ceil
from time import time
from typing import Any
from zoneinfo import ZoneInfo

from openslides_backend.action.actions.speaker.speech_state import SpeechState
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class TestSpeakerPause(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.models: dict[str, dict[str, Any]] = {
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
                "meeting_id": 1,
                "begin_time": datetime.now() - timedelta(seconds=100),
            },
        }
        self.set_models(self.models)

    def add_coupled_countdown(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_couple_countdown": True,
                    "list_of_speakers_countdown_id": 75,
                },
                "projector_countdown/75": {
                    "title": "aTenshion",
                    "running": True,
                    "default_time": 200,
                    "countdown_time": round(time()) + 100,
                    "meeting_id": 1,
                },
            }
        )

    def test_pause_correct(self) -> None:
        start = datetime.now(tz=ZoneInfo("UTC"))
        response = self.request("speaker.pause", {"id": 890})
        end = datetime.now(tz=ZoneInfo("UTC"))
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        assert start <= model["pause_time"] <= end

    def test_pause_not_started(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "begin_time": None,
                },
            }
        )
        response = self.request("speaker.pause", {"id": 890})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Speaker is not currently speaking.",
            response.json["message"],
        )

    def test_pause_already_paused(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "pause_time": datetime.now(),
                },
            }
        )
        response = self.request("speaker.pause", {"id": 890})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Speaker is not currently speaking.",
            response.json["message"],
        )

    def test_pause_ended(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "end_time": datetime.now(),
                },
            }
        )
        response = self.request("speaker.pause", {"id": 890})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Speaker is not currently speaking.",
            response.json["message"],
        )

    def test_pause_update_countdown(self) -> None:
        start = time()
        self.add_coupled_countdown()
        response = self.request("speaker.pause", {"id": 890})
        end = time()
        self.assert_status_code(response, 200)
        countdown = self.get_model("projector_countdown/75")
        assert countdown.get("running") is False
        self.assertAlmostEqual(countdown["countdown_time"], 100, delta=end - start)

    def setup_structure_level_and_speaker(self) -> None:
        self.set_models(
            {
                "structure_level/1": {
                    "name": "dps",
                    "meeting_id": 1,
                },
                "structure_level_list_of_speakers/2": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                    "structure_level_id": 1,
                    "initial_time": 600,
                    "remaining_time": 200,
                },
                "speaker/890": {
                    "structure_level_list_of_speakers_id": 2,
                    "total_pause": 20,
                },
            }
        )

    def test_pause_with_structure_level(self) -> None:
        self.setup_structure_level_and_speaker()
        start = datetime.now()
        response = self.request("speaker.pause", {"id": 890})
        end = datetime.now()
        self.assert_status_code(response, 200)
        model = self.get_model("structure_level_list_of_speakers/2")
        self.assertEqual(model.get("current_start_time"), None)
        self.assertAlmostEqual(model["remaining_time"], 100, delta=end - start)

    def test_pause_with_structure_level_and_unpause_time(self) -> None:
        self.setup_structure_level_and_speaker()
        self.set_models(
            {
                "speaker/890": {
                    "unpause_time": datetime.now() - timedelta(seconds=10),
                },
            }
        )
        start = datetime.now()
        response = self.request("speaker.pause", {"id": 890})
        end = datetime.now()
        self.assert_status_code(response, 200)
        model = self.get_model("structure_level_list_of_speakers/2")
        self.assertAlmostEqual(
            model["remaining_time"], 190, delta=ceil((end - start).total_seconds())
        )

    def pause_with_speech_state(self, state: SpeechState) -> None:
        self.setup_structure_level_and_speaker()
        self.set_models({"speaker/890": {"speech_state": state}})
        response = self.request("speaker.pause", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/2", {"remaining_time": 200}
        )

    def test_pause_with_interposed_question(self) -> None:
        self.pause_with_speech_state(SpeechState.INTERPOSED_QUESTION)

    def test_pause_with_intervention(self) -> None:
        self.pause_with_speech_state(SpeechState.INTERVENTION)

    def test_pause_with_point_of_order(self) -> None:
        self.setup_structure_level_and_speaker()
        self.set_models({"speaker/890": {"point_of_order": True}})
        response = self.request("speaker.pause", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/2", {"remaining_time": 200}
        )

    def test_pause_no_permissions(self) -> None:
        self.base_permission_test(self.models, "speaker.pause", {"id": 890})

    def test_pause_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "speaker.pause",
            {"id": 890},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_pause_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.models,
            "speaker.pause",
            {"id": 890},
        )
