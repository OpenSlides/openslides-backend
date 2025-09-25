from datetime import datetime
from zoneinfo import ZoneInfo

from tests.system.action.base import BaseActionTestCase


class MeetingUserDelete(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(10)

    def test_delete(self) -> None:
        self.set_models({"meeting_user/5": {"user_id": 1, "meeting_id": 10}})
        response = self.request("meeting_user.delete", {"id": 5})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting_user/5")

    def test_delete_with_speaker(self) -> None:
        """Also checks that the user is successfully removed from a meeting he was present in."""
        self.create_meeting(101)
        self.set_models(
            {
                "meeting/10": {"present_user_ids": [1]},
                "meeting/101": {"present_user_ids": [1]},
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "topic/11": {
                    "title": "tipic",
                    "sequential_number": 11,
                    "meeting_id": 10,
                },
                "agenda_item/6": {"content_object_id": "topic/11", "meeting_id": 101},
                "list_of_speakers/11": {
                    "sequential_number": 11,
                    "content_object_id": "topic/11",
                    "meeting_id": 10,
                },
                "speaker/1": {
                    "meeting_user_id": 5,
                    "list_of_speakers_id": 11,
                    "meeting_id": 10,
                },
                "speaker/2": {
                    "meeting_user_id": 5,
                    "meeting_id": 10,
                    "list_of_speakers_id": 11,
                    "begin_time": datetime.fromtimestamp(123456),
                },
            }
        )
        response = self.request("meeting_user.delete", {"id": 5})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting_user/5")
        self.assert_model_not_exists("speaker/1")
        self.assert_model_exists(
            "speaker/2",
            {
                "meeting_id": 10,
                "begin_time": datetime.fromtimestamp(123456, ZoneInfo("UTC")),
            },
        )
        self.assert_model_exists(
            "user/1", {"is_present_in_meeting_ids": [101], "meeting_user_ids": None}
        )
        self.assert_model_exists("meeting/10", {"present_user_ids": None})
        self.assert_model_exists("meeting/101", {"present_user_ids": [1]})

    def test_delete_with_editor_and_working_group_speaker(self) -> None:
        self.set_models(
            {
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "list_of_speakers/12": {
                    "sequential_number": 12,
                    "content_object_id": "motion/11",
                    "meeting_id": 10,
                },
                "motion/11": {
                    "title": "morse",
                    "sequential_number": 11,
                    "state_id": 10,
                    "meeting_id": 10,
                },
                "motion_editor/1": {
                    "meeting_user_id": 5,
                    "motion_id": 11,
                    "meeting_id": 10,
                },
                "motion_working_group_speaker/2": {
                    "meeting_user_id": 5,
                    "motion_id": 11,
                    "meeting_id": 10,
                },
            }
        )
        response = self.request("meeting_user.delete", {"id": 5})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting_user/5")
        self.assert_model_not_exists("motion_editor/1")
        self.assert_model_not_exists("motion_working_group_speaker/2")
        self.assert_model_exists(
            "meeting/10",
            {"motion_editor_ids": None, "motion_working_group_speaker_ids": None},
        )

    def test_delete_with_chat_message(self) -> None:
        self.set_models(
            {
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "chat_group/1": {"name": "cg1", "meeting_id": 10},
                "chat_message/1": {
                    "content": "message",
                    "created": datetime.fromtimestamp(1234567890),
                    "meeting_user_id": 5,
                    "chat_group_id": 1,
                    "meeting_id": 10,
                },
                "chat_message/2": {
                    "content": "message",
                    "created": datetime.fromtimestamp(1234567891),
                    "meeting_user_id": 5,
                    "chat_group_id": 1,
                    "meeting_id": 10,
                },
            }
        )
        response = self.request("meeting_user.delete", {"id": 5})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting_user/5")
        self.assert_model_exists("chat_message/1", {"meeting_user_id": None})
        self.assert_model_exists("chat_message/2", {"meeting_user_id": None})
