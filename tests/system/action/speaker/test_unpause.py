from datetime import datetime, timedelta
from math import ceil, floor
from time import time
from typing import Any
from zoneinfo import ZoneInfo

from openslides_backend.action.actions.speaker.speech_state import SpeechState
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class TestSpeakerUnpause(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.models: dict[str, dict[str, Any]] = {
            "user/7": {"username": "test_username1"},
            "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
            "topic/1337": {
                "title": "introduction leet gathering",
                "sequential_number": 1337,
                "meeting_id": 1,
            },
            "agenda_item/1": {"content_object_id": "topic/1337", "meeting_id": 1},
            "list_of_speakers/23": {
                "sequential_number": 23,
                "content_object_id": "topic/1337",
                "meeting_id": 1,
            },
            "speaker/890": {
                "meeting_user_id": 7,
                "list_of_speakers_id": 23,
                "meeting_id": 1,
                "begin_time": datetime.now() - timedelta(seconds=100),
                "pause_time": datetime.now() - timedelta(seconds=50),
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
                    "title": "pc",
                    "running": False,
                    "default_time": 200,
                    "countdown_time": 100,
                    "meeting_id": 1,
                },
            }
        )

    def test_unpause_correct(self) -> None:
        start = time()
        response = self.request("speaker.unpause", {"id": 890})
        end = time()
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        self.assertIsNone(model.get("pause_time"), None)
        self.assertAlmostEqual(model["total_pause"], 50, delta=end - start)

    def test_unpause_not_started(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "begin_time": None,
                    "pause_time": None,
                },
            }
        )
        response = self.request("speaker.unpause", {"id": 890})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Speaker is not paused.",
            response.json["message"],
        )

    def test_unpause_not_paused(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "pause_time": None,
                },
            }
        )
        response = self.request("speaker.unpause", {"id": 890})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Speaker is not paused.",
            response.json["message"],
        )

    def test_unpause_ended(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "end_time": datetime.now(),
                },
            }
        )
        response = self.request("speaker.unpause", {"id": 890})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Speaker is not paused.",
            response.json["message"],
        )

    def test_unpause_update_countdown(self) -> None:
        self.add_coupled_countdown()
        now = floor(time())
        response = self.request("speaker.unpause", {"id": 890})
        self.assert_status_code(response, 200)
        countdown = self.get_model("projector_countdown/75")
        assert countdown.get("running") is True
        assert now <= countdown["countdown_time"] - 100 <= ceil(time())

    def setup_structure_level_with_speaker(self) -> None:
        self.set_models(
            {
                "structure_level/1": {
                    "name": "UDC",
                    "meeting_id": 1,
                },
                "structure_level_list_of_speakers/2": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 23,
                    "structure_level_id": 1,
                    "initial_time": 299,
                    "remaining_time": 100,
                },
                "speaker/890": {
                    "structure_level_list_of_speakers_id": 2,
                    "total_pause": 20,
                },
            }
        )

    def test_unpause_with_structure_level(self) -> None:
        self.setup_structure_level_with_speaker()
        start = datetime.now(ZoneInfo("UTC"))
        response = self.request("speaker.unpause", {"id": 890})
        self.assert_status_code(response, 200)
        model = self.get_model("structure_level_list_of_speakers/2")
        self.assertGreaterEqual(model["current_start_time"], start)
        self.assertEqual(model["remaining_time"], 100)

    def test_unpause_intervention_with_structure_level(self) -> None:
        self.setup_structure_level_with_speaker()
        self.set_models({"speaker/890": {"speech_state": SpeechState.INTERVENTION}})
        response = self.request("speaker.unpause", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/2", {"current_start_time": None}
        )

    def test_unpause_point_of_order_with_structure_level(self) -> None:
        self.setup_structure_level_with_speaker()
        self.set_models({"speaker/890": {"point_of_order": True}})
        response = self.request("speaker.unpause", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/2", {"current_start_time": None}
        )

    def test_unpause_interposed_question_with_structure_level(self) -> None:
        self.setup_structure_level_with_speaker()
        self.set_models(
            {"speaker/890": {"speech_state": SpeechState.INTERPOSED_QUESTION}}
        )
        response = self.request("speaker.unpause", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/2", {"current_start_time": None}
        )

    def test_unpause_no_permissions(self) -> None:
        self.base_permission_test(self.models, "speaker.unpause", {"id": 890})

    def test_unpause_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "speaker.unpause",
            {"id": 890},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_unpause_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.models,
            "speaker.unpause",
            {"id": 890},
        )
