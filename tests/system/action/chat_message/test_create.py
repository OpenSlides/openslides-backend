from time import time

from tests.system.action.base import BaseActionTestCase


class ChatMessageCreate(BaseActionTestCase):
    def test_no_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "chat_group/2": {"meeting_id": 1, "write_group_ids": [3]},
                "group/3": {"meeting_id": 1, "user_ids": []},
            }
        )
        response = self.request(
            "chat_message.create", {"chat_group_id": 2, "content": "<b>test</b>"}
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to write in this chat group."
            in response.json["message"]
        )

    def test_create_correct(self) -> None:
        start_time = int(time())
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "chat_group/2": {"meeting_id": 1, "write_group_ids": [3]},
                "group/3": {"meeting_id": 1, "user_ids": [1]},
                "user/1": {"group_$_ids": ["1"], "group_$1_ids": [3]},
            }
        )
        response = self.request(
            "chat_message.create", {"chat_group_id": 2, "content": "test"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("chat_message/1")
        assert model.get("created", -1) >= start_time
        assert model.get("content") == "test"
        assert model.get("chat_group_id") == 2
        self.assert_model_exists("chat_group/2", {"chat_message_ids": [1]})
