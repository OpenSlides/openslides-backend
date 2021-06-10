from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ChatGroupUpdate(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: Dict[str, Dict[str, Any]] = {
            "meeting/1": {"enable_chat": True},
            "chat_group/1": {
                "meeting_id": 1,
                "name": "redekreis1",
                "read_group_ids": [1],
                "write_group_ids": [2],
            },
            "group/1": {"meeting_id": 1, "read_chat_group_ids": [1]},
            "group/2": {"meeting_id": 1, "write_chat_group_ids": [1]},
            "group/3": {"meeting_id": 1},
        }

    def test_update(self) -> None:
        self.set_models(self.test_models)
        response = self.request(
            "chat_group.update",
            {"id": 1, "name": "test", "read_group_ids": [2], "write_group_ids": [2, 3]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "chat_group/1",
            {"name": "test", "read_group_ids": [2], "write_group_ids": [2, 3]},
        )
        self.assert_model_exists("group/1", {"read_chat_group_ids": []})
        self.assert_model_exists(
            "group/2", {"read_chat_group_ids": [1], "write_chat_group_ids": [1]}
        )
        self.assert_model_exists("group/3", {"write_chat_group_ids": [1]})

    def test_update_not_enabled(self) -> None:
        self.test_models["meeting/1"]["enable_chat"] = False
        self.set_models(self.test_models)
        response = self.request("chat_group.update", {"id": 1, "name": "test"})
        self.assert_status_code(response, 400)
        assert "Chat is not enabled." in response.json["message"]

    def test_update_group_from_different_meeting(self) -> None:
        self.set_models(
            {
                "meeting/1": {"enable_chat": True},
                "meeting/2": {},
                "chat_group/1": {
                    "meeting_id": 1,
                    "name": "redekreis1",
                },
                "group/1": {"meeting_id": 2},
            }
        )
        response = self.request(
            "chat_group.update",
            {"id": 1, "name": "test", "read_group_ids": [1], "write_group_ids": [1]},
        )
        self.assert_status_code(response, 400)
        assert (
            "The following models do not belong to meeting 1: ['group/1']"
            in response.json["message"]
        )

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            self.test_models, "chat_group.update", {"id": 1, "name": "test"}
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "chat_group.update",
            {"id": 1, "name": "test"},
            Permissions.Chat.CAN_MANAGE,
        )
