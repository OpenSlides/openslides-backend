from tests.system.action.base import BaseActionTestCase


class ChatMessageUpdate(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [7],
                },
                "chat_message/2": {
                    "meeting_user_id": 7,
                    "content": "blablabla",
                    "meeting_id": 1,
                },
                "meeting_user/7": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "chat_message_ids": [2],
                },
                "user/1": {"meeting_user_ids": [7]},
            }
        )
        response = self.request("chat_message.update", {"id": 2, "content": "test"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("chat_message/2", {"content": "test"})

    def test_update_no_permissions(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "user/2": {},
                "chat_message/2": {
                    "meeting_user_id": 8,
                    "content": "blablabla",
                    "meeting_id": 1,
                },
                "meeting_user/8": {
                    "meeting_id": 1,
                    "user_id": 2,
                    "chat_message_ids": [2],
                },
                "user/1": {"meeting_user_ids": [7]},
            }
        )
        response = self.request("chat_message.update", {"id": 2, "content": "test"})
        self.assert_status_code(response, 403)
        assert (
            "You must be creator of a chat message to edit it."
            in response.json["message"]
        )
