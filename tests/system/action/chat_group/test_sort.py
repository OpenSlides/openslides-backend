from typing import Any

from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class ChatGroupSortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            ONE_ORGANIZATION_FQID: {"enable_chat": True},
            "meeting/1": {"is_active_in_organization_id": 1},
            "chat_group/31": {
                "meeting_id": 1,
                "name": "name_loisueb",
            },
            "chat_group/32": {
                "meeting_id": 1,
                "name": "name_blanumop",
            },
        }

    def test_sort_correct(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "chat_group/31": {
                    "meeting_id": 222,
                    "name": "name_loisueb",
                },
                "chat_group/32": {
                    "meeting_id": 222,
                    "name": "name_blanumop",
                },
            }
        )
        response = self.request(
            "chat_group.sort",
            {"meeting_id": 222, "chat_group_ids": [32, 31]},
        )
        self.assert_status_code(response, 200)
        model_31 = self.get_model("chat_group/31")
        assert model_31.get("weight") == 2
        model_32 = self.get_model("chat_group/32")
        assert model_32.get("weight") == 1

    def test_sort_not_enabled(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": False},
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "chat_group/31": {
                    "meeting_id": 222,
                    "name": "name_loisueb",
                },
            }
        )
        response = self.request(
            "chat_group.sort",
            {"meeting_id": 222, "chat_group_ids": [31]},
        )
        self.assert_status_code(response, 400)
        assert "Chat is not enabled." in response.json["message"]

    def test_sort_missing_model(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "chat_group/31": {
                    "meeting_id": 222,
                    "name": "name_loisueb",
                },
            }
        )
        response = self.request(
            "chat_group.sort",
            {"meeting_id": 222, "chat_group_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        assert (
            "chat_group sorting failed, because element chat_group/32 doesn't exist."
            in response.json["message"]
        )

    def test_sort_additional_chat_groups_in_meeting(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "chat_group/31": {
                    "meeting_id": 222,
                    "name": "name_loisueb",
                },
                "chat_group/32": {
                    "meeting_id": 222,
                    "name": "name_blanumop",
                },
                "chat_group/33": {
                    "meeting_id": 222,
                    "name": "name_polusiem",
                },
            }
        )
        response = self.request(
            "chat_group.sort",
            {"meeting_id": 222, "chat_group_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        assert (
            "chat_group sorting failed, because some elements were not included in the call."
            in response.json["message"]
        )

    def test_sort_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "chat_group.sort",
            {"meeting_id": 1, "chat_group_ids": [32, 31]},
        )

    def test_sort_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "chat_group.sort",
            {"meeting_id": 1, "chat_group_ids": [32, 31]},
            Permissions.Chat.CAN_MANAGE,
        )

    def test_sort_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "chat_group.sort",
            {"meeting_id": 1, "chat_group_ids": [32, 31]},
        )
