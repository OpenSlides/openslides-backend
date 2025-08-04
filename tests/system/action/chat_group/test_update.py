from typing import Any

from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class ChatGroupUpdate(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.test_models: dict[str, dict[str, Any]] = {
            ONE_ORGANIZATION_FQID: {"enable_chat": True},
            "chat_group/1": {
                "meeting_id": 1,
                "name": "redekreis1",
                "read_group_ids": [1],
                "write_group_ids": [2],
            },
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
        self.assert_model_exists("group/1", {"read_chat_group_ids": None})
        self.assert_model_exists(
            "group/2", {"read_chat_group_ids": [1], "write_chat_group_ids": [1]}
        )
        self.assert_model_exists("group/3", {"write_chat_group_ids": [1]})

    def test_update_not_enabled(self) -> None:
        self.test_models[ONE_ORGANIZATION_FQID]["enable_chat"] = False
        self.set_models(self.test_models)
        response = self.request("chat_group.update", {"id": 1, "name": "test"})
        self.assert_status_code(response, 400)
        assert "Chat is not enabled." in response.json["message"]

    def test_update_group_from_different_meeting(self) -> None:
        self.create_meeting()
        self.create_meeting(2)
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "chat_group/1": {"meeting_id": 1, "name": "redekreis1"},
            }
        )
        response = self.request(
            "chat_group.update",
            {"id": 1, "name": "test", "read_group_ids": [4], "write_group_ids": [4]},
        )
        self.assert_status_code(response, 400)
        assert (
            "The following models do not belong to meeting 1: ['group/4']"
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

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.test_models, "chat_group.update", {"id": 1, "name": "test"}
        )

    def test_update_not_unique_name(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "chat_group/1": {"meeting_id": 1, "name": "redekreis1"},
                "chat_group/2": {"meeting_id": 1, "name": "test"},
            }
        )
        response = self.request("chat_group.update", {"id": 1, "name": "test"})
        self.assert_status_code(response, 400)
        assert "The name of a chat group must be unique." == response.json["message"]

    def test_update_anonymous_may_read(self) -> None:
        self.set_models(self.test_models)
        anonymous_group = self.set_anonymous()
        response = self.request(
            "chat_group.update", {"id": 1, "read_group_ids": [anonymous_group]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("chat_group/1", {"read_group_ids": [anonymous_group]})

    def test_update_anonymous_may_not_write(self) -> None:
        self.set_models(self.test_models)
        anonymous_group = self.set_anonymous()
        response = self.request(
            "chat_group.update",
            {
                "id": 1,
                "write_group_ids": [anonymous_group],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Anonymous group is not allowed in write_group_ids.",
            response.json["message"],
        )
