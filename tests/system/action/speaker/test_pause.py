from math import ceil, floor
from time import time
from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class TestSpeakerPause(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.models: Dict[str, Dict[str, Any]] = {
            "meeting/1": {"is_active_in_organization_id": 1},
            "user/7": {"username": "test_username1"},
            "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
            "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 1},
            "speaker/890": {
                "meeting_user_id": 7,
                "list_of_speakers_id": 23,
                "meeting_id": 1,
                "begin_time": floor(time()) - 100,
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
                    "running": True,
                    "default_time": 200,
                    "countdown_time": floor(time()) + 100,
                    "meeting_id": 1,
                },
            }
        )

    def test_pause_correct(self) -> None:
        start = floor(time())
        response = self.request("speaker.pause", {"id": 890})
        end = ceil(time())
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
                    "pause_time": floor(time()),
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
                    "end_time": floor(time()),
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
        self.add_coupled_countdown()
        now = floor(time())
        response = self.request("speaker.pause", {"id": 890})
        self.assert_status_code(response, 200)
        countdown = self.get_model("projector_countdown/75")
        assert countdown.get("running") is False
        self.assertAlmostEqual(
            countdown["countdown_time"], 100, delta=ceil(time()) - now
        )

    def test_pause_with_structure_level(self) -> None:
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
                    "remaining_time": 100,
                },
                "list_of_speakers/23": {"structure_level_list_of_speakers_ids": [2]},
                "speaker/890": {
                    "structure_level_list_of_speakers_id": 2,
                    "total_pause": 20,
                },
            }
        )
        start = floor(time())
        response = self.request("speaker.pause", {"id": 890})
        end = ceil(time())
        self.assert_status_code(response, 200)
        model = self.get_model("structure_level_list_of_speakers/2")
        self.assertEqual(model.get("current_start_time"), None)
        self.assertAlmostEqual(model["remaining_time"], 20, delta=end - start)

    def test_pause_no_permissions(self) -> None:
        self.base_permission_test(self.models, "speaker.pause", {"id": 890})

    def test_pause_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "speaker.pause",
            {"id": 890},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )
