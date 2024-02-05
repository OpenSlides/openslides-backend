import time
from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class SpeakerSpeakTester(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "user/7": {"username": "test_username1"},
            "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
            "list_of_speakers/23": {"speaker_ids": [890], "meeting_id": 1},
            "speaker/890": {
                "meeting_user_id": 7,
                "list_of_speakers_id": 23,
                "meeting_id": 1,
            },
        }

    def test_speak_correct(self) -> None:
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
        response = self.request("speaker.speak", {"id": 890})
        self.assert_status_code(response, 200)
        model = self.get_model("speaker/890")
        self.assertTrue(model.get("begin_time") is not None)

    def test_speak_wrong_id(self) -> None:
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
        response = self.request("speaker.speak", {"id": 889})
        self.assert_status_code(response, 400)
        model = self.get_model("speaker/890")
        self.assertTrue(model.get("begin_time") is None)

    def test_speak_existing_speaker(self) -> None:
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
                    "meeting_id": 1,
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
                "meeting/1": {"is_active_in_organization_id": 1},
                "user/7": {"username": "test_username1"},
                "meeting_user/7": {
                    "meeting_id": 1,
                    "user_id": 7,
                    "speaker_ids": [890, 891],
                },
                "list_of_speakers/23": {"speaker_ids": [890, 891], "meeting_id": 1},
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "begin_time": 100000,
                    "meeting_id": 1,
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
        self.assertTrue(model2.get("begin_time") is not None)
        model1 = self.get_model("speaker/890")
        self.assertEqual(model1.get("end_time"), model2["begin_time"])

    def test_closed(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "user/7": {"username": "test_username1"},
                "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
                "list_of_speakers/23": {
                    "speaker_ids": [890],
                    "closed": True,
                    "meeting_id": 1,
                },
                "speaker/890": {
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("speaker.speak", {"id": 890})
        self.assert_status_code(response, 200)
        speaker = self.get_model("speaker/890")
        self.assertIsNotNone(speaker.get("begin_time"))

    def test_speak_update_countdown(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "list_of_speakers_couple_countdown": True,
                    "list_of_speakers_countdown_id": 75,
                    "is_active_in_organization_id": 1,
                },
                "projector_countdown/75": {
                    "running": False,
                    "default_time": 60,
                    "countdown_time": 30.0,
                    "meeting_id": 1,
                },
                "user/7": {"username": "test_username1"},
                "meeting_user/7": {"meeting_id": 1, "user_id": 7, "speaker_ids": [890]},
                "list_of_speakers/23": {"meeting_id": 1, "speaker_ids": [890]},
                "speaker/890": {
                    "meeting_id": 1,
                    "meeting_user_id": 7,
                    "list_of_speakers_id": 23,
                },
            }
        )
        response = self.request("speaker.speak", {"id": 890})
        self.assert_status_code(response, 200)
        countdown = self.get_model("projector_countdown/75")
        assert countdown.get("running")
        now = time.time()
        assert now <= countdown.get("countdown_time", 0.0) <= now + 300

    def test_speak_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models, "speaker.speak", {"id": 890}
        )

    def test_speak_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "speaker.speak",
            {"id": 890},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )
