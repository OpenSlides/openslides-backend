from math import ceil, floor
from time import time
from typing import Any

from openslides_backend.action.actions.speaker.speech_state import SpeechState
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class SpeakerSpeakTester(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.models: dict[str, dict[str, Any]] = {
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
        self.set_models(self.models)

    def add_coupled_countdown(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_couple_countdown": True,
                    "list_of_speakers_countdown_id": 75,
                },
                "projector_countdown/75": {
                    "running": False,
                    "default_time": 60,
                    "countdown_time": 30.0,
                    "meeting_id": 1,
                },
            }
        )

    def test_speak_correct(self) -> None:
        response = self.request("speaker.speak", {"id": 890})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        self.assertIsNotNone(model.get("begin_time"))

    def test_speak_wrong_id(self) -> None:
        response = self.request("speaker.speak", {"id": 889})
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertIsNone(model.get("begin_time"))

    def test_speak_existing_speaker(self) -> None:
        self.set_models(
            {
                "speaker/890": {
                    "begin_time": 100000,
                },
            }
        )
        response = self.request("speaker.speak", {"id": 890})
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertEqual(model.get("begin_time"), 100000)

    def test_speak_next_speaker(self) -> None:
        self.set_models(
            {
                "meeting_user/7": {
                    "speaker_ids": [890, 891],
                },
                "list_of_speakers/23": {"speaker_ids": [890, 891]},
                "speaker/890": {
                    "begin_time": 100000,
                },
                "speaker/891": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("speaker.speak", {"id": 891})
        self.assert_status_code(response, 200)
        model2 = self.get_model("speaker/891")
        self.assertIsNotNone(model2.get("begin_time"))
        model1 = self.get_model("speaker/890")
        self.assertEqual(model1.get("end_time"), model2["begin_time"])

    def test_closed(self) -> None:
        self.set_models(
            {
                "list_of_speakers/23": {
                    "closed": True,
                },
            }
        )
        response = self.request("speaker.speak", {"id": 890})
        self.assert_status_code(response, 200)
        speaker = self.get_model("speaker/890")
        self.assertIsNotNone(speaker.get("begin_time"))

    def test_speak_update_countdown(self) -> None:
        self.add_coupled_countdown()
        now = floor(time())
        response = self.request("speaker.speak", {"id": 890})
        self.assert_status_code(response, 200)
        countdown = self.get_model("projector_countdown/75")
        assert countdown.get("running")
        assert now <= countdown["countdown_time"] - 60 <= ceil(time())

    def test_speak_intervention(self) -> None:
        self.add_coupled_countdown()
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_intervention_time": 100,
                },
                "speaker/890": {
                    "speech_state": SpeechState.INTERVENTION,
                },
            }
        )
        now = floor(time())
        response = self.request("speaker.speak", {"id": 890})
        self.assert_status_code(response, 200)
        countdown = self.assert_model_exists(
            "projector_countdown/75",
            {
                "running": True,
                "default_time": 100,
            },
        )
        assert now <= countdown["countdown_time"] - 100 <= ceil(time())

    def test_speak_interposed_question(self) -> None:
        self.add_coupled_countdown()
        self.set_models(
            {
                "speaker/890": {
                    "speech_state": SpeechState.INTERPOSED_QUESTION,
                },
            }
        )
        now = floor(time())
        response = self.request("speaker.speak", {"id": 890})
        self.assert_status_code(response, 200)
        countdown = self.assert_model_exists(
            "projector_countdown/75",
            {
                "running": True,
                "default_time": 0,
            },
        )
        assert now <= countdown["countdown_time"] <= ceil(time())

    def test_speak_with_interposed_questions(self) -> None:
        now = floor(time())
        self.set_models(
            {
                "meeting_user/7": {
                    "speaker_ids": [890, 891, 892],
                },
                "list_of_speakers/23": {"speaker_ids": [890, 891, 892]},
                "speaker/890": {
                    "begin_time": now - 100,
                },
                "speaker/891": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                    "speech_state": SpeechState.INTERPOSED_QUESTION,
                },
            }
        )
        response = self.request("speaker.speak", {"id": 891})
        self.assert_status_code(response, 200)
        speaker = self.get_model("speaker/891")
        self.assertIsNotNone(speaker.get("begin_time"))
        speaker = self.get_model("speaker/890")
        self.assertIsNone(speaker.get("end_time"))
        self.assertIsNotNone(speaker.get("pause_time"))

    def test_speak_interposed_question_paused_current_speaker(self) -> None:
        now = floor(time())
        self.set_models(
            {
                "meeting_user/7": {
                    "speaker_ids": [890, 891],
                },
                "list_of_speakers/23": {"speaker_ids": [890, 891]},
                "speaker/890": {
                    "begin_time": now - 200,
                    "pause_time": now - 100,
                },
                "speaker/891": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                    "speech_state": SpeechState.INTERPOSED_QUESTION,
                },
                "speaker/892": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                    "speech_state": SpeechState.INTERPOSED_QUESTION,
                },
            }
        )
        # start first interposed question
        response = self.request("speaker.speak", {"id": 891})
        self.assert_status_code(response, 200)
        speaker = self.get_model("speaker/891")
        self.assertIsNotNone(speaker.get("begin_time"))
        speaker = self.get_model("speaker/890")
        self.assertIsNone(speaker.get("end_time"))
        self.assertIsNotNone(speaker.get("pause_time"))

        # start second interposed question
        response = self.request("speaker.speak", {"id": 892})
        self.assert_status_code(response, 200)
        for id in (890, 891):
            speaker = self.get_model(f"speaker/{id}")
            self.assertIsNone(speaker.get("end_time"))
            self.assertIsNotNone(speaker.get("pause_time"))

        # start main speaker again
        response = self.request("speaker.unpause", {"id": 890})
        self.assert_status_code(response, 200)
        for id in (891, 892):
            speaker = self.get_model(f"speaker/{id}")
            self.assertIsNone(speaker.get("end_time"))
            self.assertIsNotNone(speaker.get("pause_time"))

    def test_speak_with_structure_level(self) -> None:
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
                },
            }
        )
        now = floor(time())
        response = self.request("speaker.speak", {"id": 890})
        self.assert_status_code(response, 200)
        model = self.get_model("structure_level_list_of_speakers/2")
        self.assertEqual(model["remaining_time"], 100)
        assert now <= model["current_start_time"] <= ceil(time())

    def test_speak_with_structure_level_and_current_speaker(self) -> None:
        now = floor(time())
        self.set_models(
            {
                "meeting/1": {
                    "structure_level_ids": [1],
                    "structure_level_list_of_speakers_ids": [2],
                },
                "meeting_user/7": {
                    "speaker_ids": [889, 890],
                },
                "list_of_speakers/23": {
                    "speaker_ids": [889, 890],
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
                    "speaker_ids": [889, 890],
                    "remaining_time": 500,
                },
                "speaker/889": {
                    "structure_level_list_of_speakers_id": 2,
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                    "begin_time": now - 100,
                },
                "speaker/890": {
                    "structure_level_list_of_speakers_id": 2,
                },
            }
        )
        response = self.request("speaker.speak", {"id": 890})
        self.assert_status_code(response, 200)
        speaker = self.get_model("speaker/889")
        model = self.get_model("structure_level_list_of_speakers/2")
        self.assertEqual(
            model["remaining_time"], 500 - (speaker["end_time"] - speaker["begin_time"])
        )
        assert now <= model["current_start_time"] <= ceil(time())

    def speak_with_structure_level_and_speech_state(self, state: SpeechState) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "structure_level_ids": [1],
                    "structure_level_list_of_speakers_ids": [2],
                    "list_of_speakers_intervention_time": 100,
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
                    "speech_state": state,
                },
            }
        )
        response = self.request("speaker.speak", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/2", {"current_start_time": None}
        )

    def test_speak_with_structure_level_and_speech_state_intervention(self) -> None:
        self.speak_with_structure_level_and_speech_state(SpeechState.INTERVENTION)

    def test_speak_with_structure_level_and_speech_state_interposed_question(
        self,
    ) -> None:
        self.speak_with_structure_level_and_speech_state(
            SpeechState.INTERPOSED_QUESTION
        )

    def test_speak_no_permissions(self) -> None:
        self.base_permission_test(self.models, "speaker.speak", {"id": 890})

    def test_speak_permissions(self) -> None:
        self.base_permission_test(
            self.models,
            "speaker.speak",
            {"id": 890},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_speak_with_structure_level_and_point_of_order(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "structure_level_ids": [1],
                    "structure_level_list_of_speakers_ids": [2],
                    "list_of_speakers_intervention_time": 100,
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
                    "point_of_order": True,
                },
            }
        )
        response = self.request("speaker.speak", {"id": 890})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "structure_level_list_of_speakers/2", {"current_start_time": None}
        )
