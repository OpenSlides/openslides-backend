from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ChatMessageDelete(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: Dict[str, Dict[str, Any]] = {
            "meeting/1": {"is_active_in_organization_id": 1, "meeting_user_ids": [5]},
            "chat_group/11": {"meeting_id": 1, "name": "test"},
            "chat_message/101": {"meeting_id": 1, "meeting_user_id": 5},
            "meeting_user/5": {
                "meeting_id": 1,
                "user_id": 3,
                "chat_message_ids": [101],
            },
            "user/3": {"username": "username_xx", "meeting_user_ids": [5]},
        }

    def test_delete_correct_own_msg(self) -> None:
        self.test_models["user/1"] = {"organization_management_level": None}
        self.test_models["chat_message/101"]["meeting_user_id"] = 6
        self.set_models(self.test_models)
        self.set_models(
            {
                "meeting_user/6": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "chat_message_ids": [101],
                }
            }
        )
        response = self.request("chat_message.delete", {"id": 101})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("chat_message/101")

    def test_delete_no_permission(self) -> None:
        self.base_permission_test(self.test_models, "chat_message.delete", {"id": 101})

    def test_delete_correct_permission(self) -> None:
        self.base_permission_test(
            self.test_models,
            "chat_message.delete",
            {"id": 101},
            Permissions.Chat.CAN_MANAGE,
        )
        self.assert_model_deleted("chat_message/101")
