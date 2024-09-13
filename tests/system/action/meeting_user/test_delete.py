from tests.system.action.base import BaseActionTestCase


class MeetingUserDelete(BaseActionTestCase):
    def test_delete(self) -> None:
        self.set_models(
            {
                "meeting/10": {"is_active_in_organization_id": 1},
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
            }
        )
        response = self.request("meeting_user.delete", {"id": 5})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting_user/5")

    def test_delete_with_speaker(self) -> None:
        self.set_models(
            {
                "meeting/10": {"is_active_in_organization_id": 1},
                "meeting_user/5": {
                    "user_id": 1,
                    "meeting_id": 10,
                    "speaker_ids": [1, 2],
                },
                "speaker/1": {
                    "meeting_user_id": 5,
                    "meeting_id": 10,
                },
                "speaker/2": {
                    "meeting_user_id": 5,
                    "meeting_id": 10,
                    "begin_time": 123456,
                },
            }
        )
        response = self.request("meeting_user.delete", {"id": 5})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting_user/5")
        self.assert_model_deleted("speaker/1")
        self.assert_model_exists("speaker/2", {"meeting_id": 10, "begin_time": 123456})

    def test_delete_with_chat_message(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "chat_message_ids": [1, 2],
                    "chat_group_ids": [1],
                },
                "meeting_user/5": {
                    "user_id": 1,
                    "meeting_id": 10,
                    "chat_message_ids": [1, 2],
                },
                "chat_group/1": {
                    "name": "cg1",
                    "meeting_id": 10,
                    "chat_message_ids": [1, 2],
                },
                "chat_message/1": {
                    "content": "message",
                    "created": 1234567890,
                    "meeting_user_id": 5,
                    "chat_group_id": 1,
                    "meeting_id": 10,
                },
                "chat_message/2": {
                    "content": "message",
                    "created": 1234567891,
                    "meeting_user_id": 5,
                    "chat_group_id": 1,
                    "meeting_id": 10,
                },
            }
        )
        response = self.request("meeting_user.delete", {"id": 5})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting_user/5", {"chat_message_ids": [1, 2]})
        self.assert_model_exists("chat_message/1", {"meeting_user_id": None})
        self.assert_model_exists("chat_message/2", {"meeting_user_id": None})
