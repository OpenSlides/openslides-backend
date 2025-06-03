from time import time

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ChatMessageCreate(BaseActionTestCase):
    def test_no_permission(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "chat_group/2": {"meeting_id": 1, "write_group_ids": [3]},
                "group/3": {"meeting_id": 1, "meeting_user_ids": []},
                "user/1": {"organization_management_level": None},
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

    def test_create_correct_as_superadmin(self) -> None:
        start_time = int(time())
        self.set_models(
            {
                "meeting/1": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [1],
                },
                "chat_group/2": {"meeting_id": 1, "write_group_ids": [3]},
                "group/3": {"meeting_id": 1, "meeting_user_ids": [1]},
                "user/1": {"meeting_user_ids": [1]},
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [3],
                },
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

    def test_create_correct_with_right_can_manage(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {
                    "meeting_user_ids": [1],
                },
                "chat_group/2": {"meeting_id": 1, "write_group_ids": []},
                "group/3": {
                    "meeting_id": 1,
                    "meeting_user_ids": [1],
                    "permissions": [Permissions.Chat.CAN_MANAGE],
                },
                "user/1": {
                    "meeting_user_ids": [1],
                    "organization_management_level": None,
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [3],
                },
            }
        )
        response = self.request(
            "chat_message.create", {"chat_group_id": 2, "content": "test"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "chat_message/1", {"chat_group_id": 2, "content": "test"}
        )

    def test_create_correct_with_user_in_write_group_of_chat_group(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [1],
                },
                "chat_group/2": {"meeting_id": 1, "write_group_ids": [3]},
                "group/3": {
                    "meeting_id": 1,
                    "meeting_user_ids": [1],
                    "permissions": [],
                },
                "user/1": {
                    "meeting_user_ids": [1],
                    "organization_management_level": None,
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [3],
                },
            }
        )
        response = self.request(
            "chat_message.create", {"chat_group_id": 2, "content": "test"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "chat_message/1", {"chat_group_id": 2, "content": "test"}
        )
