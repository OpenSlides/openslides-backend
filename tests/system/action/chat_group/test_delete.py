from typing import Any

from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class ChatGroupDelete(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            ONE_ORGANIZATION_FQID: {"enable_chat": True},
            "committee/2": {"meeting_ids": [1]},
            "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 2},
            "chat_group/1": {"meeting_id": 1, "name": "redekreis1"},
        }

    def test_delete(self) -> None:
        self.set_models(self.test_models)
        response = self.request("chat_group.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("chat_group/1")

    def test_delete_not_enabled(self) -> None:
        self.test_models[ONE_ORGANIZATION_FQID]["enable_chat"] = False
        self.set_models(self.test_models)
        response = self.request("chat_group.delete", {"id": 1})
        self.assert_status_code(response, 400)
        assert "Chat is not enabled." in response.json["message"]

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(self.test_models, "chat_group.delete", {"id": 1})

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "chat_group.delete",
            {"id": 1},
            Permissions.Chat.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.test_models,
            "chat_group.delete",
            {"id": 1},
        )
