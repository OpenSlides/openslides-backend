from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ChatGroupClear(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {"is_active_in_organization_id": 1},
            "chat_group/11": {
                "meeting_id": 1,
                "name": "redekreis1",
                "chat_message_ids": [111, 112, 113],
            },
            "chat_message/111": {
                "content": "test111",
                "chat_group_id": 11,
                "meeting_id": 1,
            },
            "chat_message/112": {
                "content": "test222",
                "chat_group_id": 11,
                "meeting_id": 1,
            },
            "chat_message/113": {
                "content": "test333",
                "chat_group_id": 11,
                "meeting_id": 1,
            },
        }

    def test_clear_permission(self) -> None:
        self.base_permission_test(
            self.test_models,
            "chat_group.clear",
            {"id": 11},
            Permissions.Chat.CAN_MANAGE,
        )
        self.assert_model_deleted("chat_message/111")
        self.assert_model_deleted("chat_message/112")
        self.assert_model_deleted("chat_message/113")
        self.assert_model_exists("chat_group/11", {"chat_message_ids": []})

    def test_clear_no_permission(self) -> None:
        self.base_permission_test(self.test_models, "chat_group.clear", {"id": 11})
