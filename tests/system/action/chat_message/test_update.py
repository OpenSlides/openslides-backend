from datetime import datetime

from tests.system.action.base import BaseActionTestCase


class ChatMessageUpdate(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models({"chat_group/1": {"name": "redekreis1", "meeting_id": 1}})

    def test_update_correct(self) -> None:
        self.set_models(
            {
                "chat_message/2": {
                    "chat_group_id": 1,
                    "meeting_user_id": 7,
                    "created": datetime.now(),
                    "content": "blablabla",
                    "meeting_id": 1,
                },
                "meeting_user/7": {"meeting_id": 1, "user_id": 1},
            }
        )
        response = self.request("chat_message.update", {"id": 2, "content": "test"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("chat_message/2", {"content": "test"})

    def test_update_no_permissions(self) -> None:
        self.set_models(
            {
                "user/2": {"username": "uer"},
                "chat_message/2": {
                    "chat_group_id": 1,
                    "meeting_user_id": 8,
                    "created": datetime.now(),
                    "content": "blablabla",
                    "meeting_id": 1,
                },
                "meeting_user/8": {"meeting_id": 1, "user_id": 2},
            }
        )
        response = self.request("chat_message.update", {"id": 2, "content": "test"})
        self.assert_status_code(response, 403)
        assert (
            "You must be creator of a chat message to edit it."
            in response.json["message"]
        )
