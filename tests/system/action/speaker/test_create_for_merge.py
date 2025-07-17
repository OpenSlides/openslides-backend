from datetime import datetime
from zoneinfo import ZoneInfo

from pytest import raises

from openslides_backend.action.actions.speaker.speech_state import SpeechState
from openslides_backend.shared.exceptions import ActionException
from tests.system.action.base import BaseActionTestCase


class SpeakerCreateForMergeTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(1)
        self.set_models(
            {
                "motion/357": {
                    "sequential_number": 357,
                    "state_id": 1,
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
                    "sequential_number": 1,
                    "content_object_id": "motion/357",
                    "meeting_id": 1,
                },
                "structure_level/1": {"name": "PDF", "meeting_id": 1},
                "structure_level_list_of_speakers/1": {
                    "structure_level_id": 1,
                    "meeting_id": 1,
                    "list_of_speakers_id": 1,
                    "initial_time": 100,
                    "remaining_time": 100,
                },
                "point_of_order_category/1": {
                    "text": "seconded",
                    "rank": 1,
                    "meeting_id": 1,
                },
            }
        )

    def test_create_normal(self) -> None:
        response = self.execute_action_internally(
            "speaker.create_for_merge",
            {
                "list_of_speakers_id": 1,
                "meeting_user_id": 78,
                "begin_time": datetime.fromtimestamp(20),
                "end_time": datetime.fromtimestamp(40),
                "unpause_time": datetime.fromtimestamp(1),
                "total_pause": 10,
                "weight": 1,
                "speech_state": SpeechState.PRO,
                "structure_level_list_of_speakers_id": 1,
            },
        )
        assert response == [{"id": 1}]
        self.assert_model_exists(
            "speaker/1",
            {
                "list_of_speakers_id": 1,
                "meeting_user_id": 78,
                "begin_time": datetime.fromtimestamp(20, ZoneInfo("UTC")),
                "end_time": datetime.fromtimestamp(40, ZoneInfo("UTC")),
                "unpause_time": datetime.fromtimestamp(1, ZoneInfo("UTC")),
                "total_pause": 10,
                "weight": 1,
                "speech_state": SpeechState.PRO,
                "structure_level_list_of_speakers_id": 1,
                "meeting_id": 1,
            },
        )

    def test_create_multi(self) -> None:
        response = self.execute_action_internally(
            "speaker.create_for_merge",
            {
                "list_of_speakers_id": 1,
                "meeting_user_id": 78,
                "begin_time": datetime.fromtimestamp(20),
                "end_time": datetime.fromtimestamp(40),
                "unpause_time": datetime.fromtimestamp(1),
                "total_pause": 10,
                "weight": 1,
                "speech_state": SpeechState.PRO,
                "structure_level_list_of_speakers_id": 1,
            },
        )
        assert response == [{"id": 1}]
        response = self.execute_action_internally(
            "speaker.create_for_merge",
            {
                "list_of_speakers_id": 1,
                "meeting_user_id": 78,
                "weight": 2,
                "note": "Hello",
                "point_of_order": True,
                "point_of_order_category_id": 1,
            },
        )
        assert response == [{"id": 2}]
        self.assert_model_exists(
            "speaker/1",
            {
                "list_of_speakers_id": 1,
                "meeting_user_id": 78,
                "begin_time": datetime.fromtimestamp(20, ZoneInfo("UTC")),
                "end_time": datetime.fromtimestamp(40, ZoneInfo("UTC")),
                "unpause_time": datetime.fromtimestamp(1, ZoneInfo("UTC")),
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
        with raises(ActionException) as e_info:
            self.execute_action_internally(
                "speaker.create_for_merge",
                {
                    "list_of_speakers_id": 1,
                    "meeting_user_id": 78,
                    "begin_time": datetime.fromtimestamp(20),
                    "end_time": datetime.fromtimestamp(40),
                    "unpause_time": datetime.fromtimestamp(1),
                    "total_pause": 10,
                    "weight": 1,
                    "speech_state": SpeechState.PRO,
                    "structure_level_list_of_speakers_id": 1,
                    "point_of_order": True,
                },
            )
        assert (
            e_info.value.message
            == "In list_of_speakers/1: Point of order can not be created with field(s) {'speech_state'} set"
        )

    def test_create_broken_normal_speech(self) -> None:
        with raises(ActionException) as e_info:
            self.execute_action_internally(
                "speaker.create_for_merge",
                {
                    "list_of_speakers_id": 1,
                    "meeting_user_id": 78,
                    "weight": 2,
                    "note": "Hello",
                    "point_of_order_category_id": 1,
                },
            )
        assert e_info.value.message.startswith(
            "In list_of_speakers/1: Normal speaker can not be created with field(s) {"
        )
        assert e_info.value.message.endswith("} set")
        for field in ["note", "point_of_order_category_id"]:
            self.assertIn(
                field,
                e_info.value.message,
            )

    def test_create_running_speech_error(self) -> None:
        with raises(ActionException) as e_info:
            self.execute_action_internally(
                "speaker.create_for_merge",
                {
                    "list_of_speakers_id": 1,
                    "meeting_user_id": 78,
                    "begin_time": datetime.fromtimestamp(20),
                    "weight": 1,
                    "speech_state": SpeechState.PRO,
                    "structure_level_list_of_speakers_id": 1,
                },
            )
        assert (
            e_info.value.message
            == "In list_of_speakers/1: Cannot create a running speech during merge"
        )

    def test_create_speech_with_broken_time(self) -> None:
        with raises(ActionException) as e_info:
            self.execute_action_internally(
                "speaker.create_for_merge",
                {
                    "list_of_speakers_id": 1,
                    "meeting_user_id": 78,
                    "begin_time": datetime.fromtimestamp(40),
                    "end_time": datetime.fromtimestamp(20),
                    "weight": 1,
                    "speech_state": SpeechState.PRO,
                    "structure_level_list_of_speakers_id": 1,
                },
            )
        assert (
            e_info.value.message
            == "In list_of_speakers/1: Can not create finished speaker as the end_time is before the begin_time"
        )
