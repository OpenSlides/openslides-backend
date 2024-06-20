from openslides_backend.action.actions.speaker.speech_state import SpeechState
from tests.system.action.base import BaseActionTestCase


class SpeakerCreateForMergeTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(1)
        self.set_models(
            {
                "meeting/1": {"meeting_user_ids": [78]},
                "motion/357": {
                    "title": "title_YIDYXmKj",
                    "meeting_id": 1,
                },
                "user/78": {
                    "username": "username_loetzbfg",
                    "meeting_ids": [1],
                    "meeting_user_ids": [78],
                },
                "meeting_user/78": {"meeting_id": 1, "user_id": 78},
                "list_of_speakers/1": {
                    "content_object_id": "motion/357",
                    "meeting_id": 1,
                    "structure_level_list_of_speakers_ids": [1],
                },
                "structure_level_list_of_speakers/1": {
                    "meeting_id": 1,
                    "list_of_speakers_id": 1,
                },
                "point_of_order_category/1": {"meeting_id": 1},
            }
        )

    def test_create_normal(self) -> None:
        response = self.request(
            "speaker.create_for_merge",
            {
                "list_of_speakers_id": 1,
                "meeting_user_id": 78,
                "begin_time": 20,
                "end_time": 40,
                "unpause_time": 1,
                "total_pause": 10,
                "weight": 1,
                "speech_state": SpeechState.PRO,
                "structure_level_list_of_speakers_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/1",
            {
                "list_of_speakers_id": 1,
                "meeting_user_id": 78,
                "begin_time": 20,
                "end_time": 40,
                "unpause_time": 1,
                "total_pause": 10,
                "weight": 1,
                "speech_state": SpeechState.PRO,
                "structure_level_list_of_speakers_id": 1,
                "meeting_id": 1,
            },
        )

    def test_create_multi(self) -> None:
        response = self.request_multi(
            "speaker.create_for_merge",
            [
                {
                    "list_of_speakers_id": 1,
                    "meeting_user_id": 78,
                    "begin_time": 20,
                    "end_time": 40,
                    "unpause_time": 1,
                    "total_pause": 10,
                    "weight": 1,
                    "speech_state": SpeechState.PRO,
                    "structure_level_list_of_speakers_id": 1,
                },
                {
                    "list_of_speakers_id": 1,
                    "meeting_user_id": 78,
                    "weight": 2,
                    "note": "Hello",
                    "point_of_order": True,
                    "point_of_order_category_id": 1,
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/1",
            {
                "list_of_speakers_id": 1,
                "meeting_user_id": 78,
                "begin_time": 20,
                "end_time": 40,
                "unpause_time": 1,
                "total_pause": 10,
                "weight": 1,
                "speech_state": SpeechState.PRO,
                "structure_level_list_of_speakers_id": 1,
                "meeting_id": 1,
            },
        )
        self.assert_model_exists(
            "speaker/2",
            {
                "list_of_speakers_id": 1,
                "meeting_user_id": 78,
                "weight": 2,
                "note": "Hello",
                "point_of_order": True,
                "point_of_order_category_id": 1,
                "meeting_id": 1,
            },
        )
