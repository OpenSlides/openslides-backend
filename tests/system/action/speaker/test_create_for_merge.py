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

    def test_create_broken_point_of_order(self) -> None:
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
                "point_of_order": True,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "In list_of_speakers/1: Point of order can not be created with field(s) {'speech_state'} set",
            response.json["message"],
        )

    def test_create_broken_normal_speech(self) -> None:
        response = self.request(
            "speaker.create_for_merge",
            {
                "list_of_speakers_id": 1,
                "meeting_user_id": 78,
                "weight": 2,
                "note": "Hello",
                "point_of_order_category_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        assert str(response.json["message"]).startswith(
            "In list_of_speakers/1: Normal speaker can not be created with field(s) {"
        )
        assert str(response.json["message"]).endswith("} set")
        for field in ["note", "point_of_order_category_id"]:
            self.assertIn(
                field,
                response.json["message"],
            )

    def test_create_running_speech_error(self) -> None:
        response = self.request(
            "speaker.create_for_merge",
            {
                "list_of_speakers_id": 1,
                "meeting_user_id": 78,
                "begin_time": 20,
                "weight": 1,
                "speech_state": SpeechState.PRO,
                "structure_level_list_of_speakers_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "In list_of_speakers/1: Cannot create a running speech during merge",
            response.json["message"],
        )

    def test_create_speech_with_broken_time(self) -> None:
        response = self.request(
            "speaker.create_for_merge",
            {
                "list_of_speakers_id": 1,
                "meeting_user_id": 78,
                "begin_time": 40,
                "end_time": 20,
                "weight": 1,
                "speech_state": SpeechState.PRO,
                "structure_level_list_of_speakers_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "In list_of_speakers/1: Can not create finished speaker as the end_time is before the begin_time",
            response.json["message"],
        )
