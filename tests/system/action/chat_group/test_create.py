from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class ChatGroupCreate(BaseActionTestCase):
    def test_create(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request(
            "chat_group.create", {"name": "redekreis1", "meeting_id": 1}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "chat_group/1", {"name": "redekreis1", "meeting_id": 1, "weight": 1}
        )

    def test_create_chat_not_enabled(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": False},
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request(
            "chat_group.create", {"name": "redekreis2", "meeting_id": 1}
        )
        self.assert_status_code(response, 400)
        assert "Chat is not enabled." in response.json["message"]

    def test_create_optional_fields(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "meeting/1": {"is_active_in_organization_id": 1},
                "group/1": {"meeting_id": 1},
                "group/2": {"meeting_id": 1},
            }
        )
        response = self.request(
            "chat_group.create",
            {
                "name": "redekreis1",
                "meeting_id": 1,
                "read_group_ids": [1],
                "write_group_ids": [2],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "chat_group/1",
            {
                "name": "redekreis1",
                "meeting_id": 1,
                "read_group_ids": [1],
                "write_group_ids": [2],
            },
        )

    def test_create_weight(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "meeting/1": {
                    "chat_group_ids": [1],
                    "is_active_in_organization_id": 1,
                },
                "meeting/2": {"chat_group_ids": [2], "is_active_in_organization_id": 1},
                "chat_group/1": {"meeting_id": 1, "weight": 10},
                "chat_group/2": {"meeting_id": 2, "weight": 100},
            }
        )
        response = self.request(
            "chat_group.create", {"name": "redekreis1", "meeting_id": 1}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "chat_group/3", {"name": "redekreis1", "meeting_id": 1, "weight": 11}
        )

    def test_create_group_from_different_meeting(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "meeting/1": {"is_active_in_organization_id": 1},
                "meeting/2": {},
                "group/1": {"meeting_id": 1},
                "group/2": {"meeting_id": 2},
            }
        )
        response = self.request(
            "chat_group.create",
            {
                "name": "redekreis1",
                "meeting_id": 1,
                "read_group_ids": [1],
                "write_group_ids": [2],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "The following models do not belong to meeting 1: ['group/2']"
            in response.json["message"]
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "meeting/1": {"name": "test1"},
            },
            "chat_group.create",
            {"name": "redekreis1", "meeting_id": 1},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "meeting/1": {"name": "test"},
            },
            "chat_group.create",
            {"name": "redekreis1", "meeting_id": 1},
            Permissions.Chat.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "meeting/1": {"name": "test"},
            },
            "chat_group.create",
            {"name": "redekreis1", "meeting_id": 1},
        )

    def test_create_not_unique_name(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "meeting/1": {"is_active_in_organization_id": 1},
                "chat_group/21": {"meeting_id": 1, "name": "test"},
            }
        )
        response = self.request(
            "chat_group.create",
            {
                "name": "test",
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        assert "The name of a chat group must be unique." == response.json["message"]

    def test_create_same_name_in_two_meetings(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "enable_chat": True,
                    "active_meeting_ids": [1, 2],
                },
                "meeting/1": {"is_active_in_organization_id": 1},
                "meeting/2": {"is_active_in_organization_id": 1},
                "chat_group/21": {"meeting_id": 1, "name": "test"},
            }
        )
        response = self.request(
            "chat_group.create",
            {
                "name": "test",
                "meeting_id": 2,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("chat_group/22", {"name": "test", "meeting_id": 2})
