from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class ChatGroupCreate(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True}
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
        self.create_meeting()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": False},
            }
        )
        response = self.request(
            "chat_group.create", {"name": "redekreis2", "meeting_id": 1}
        )
        self.assert_status_code(response, 400)
        assert "Chat is not enabled." in response.json["message"]

    def test_create_optional_fields(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
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
        self.create_meeting()
        self.create_meeting(4)
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
                "chat_group/1": {"name": "family dinner", "meeting_id": 1, "weight": 10},
                "chat_group/2": {"name": "working lunch", "meeting_id": 4, "weight": 100},
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
        self.create_meeting()
        self.create_meeting(4)
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
            }
        )
        response = self.request(
            "chat_group.create",
            {
                "name": "redekreis1",
                "meeting_id": 1,
                "read_group_ids": [1],
                "write_group_ids": [4],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "The following models do not belong to meeting 1: ['group/4']"
            in response.json["message"]
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True}
            },
            "chat_group.create",
            {"name": "redekreis1", "meeting_id": 1},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True}
            },
            "chat_group.create",
            {"name": "redekreis1", "meeting_id": 1},
            Permissions.Chat.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True}
            },
            "chat_group.create",
            {"name": "redekreis1", "meeting_id": 1},
        )

    def test_create_not_unique_name(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
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
        self.create_meeting()
        self.create_meeting(4)
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "enable_chat": True
                },
                "meeting/4": {"committee_id": 60},
                "chat_group/21": {"meeting_id": 1, "name": "test"},
            }
        )
        response = self.request(
            "chat_group.create",
            {
                "name": "test",
                "meeting_id": 4,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("chat_group/22", {"name": "test", "meeting_id": 4})

    def test_create_anonymous_may_read(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
            }
        )
        anonymous_group = self.set_anonymous()
        response = self.request(
            "chat_group.create",
            {
                "name": "redekreis1",
                "meeting_id": 1,
                "read_group_ids": [anonymous_group],
                "write_group_ids": [1, 2],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "chat_group/1",
            {
                "name": "redekreis1",
                "meeting_id": 1,
                "read_group_ids": [anonymous_group],
                "write_group_ids": [1, 2],
            },
        )

    def test_create_anonymous_may_not_write(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_chat": True},
            }
        )
        anonymous_group = self.set_anonymous()
        response = self.request(
            "chat_group.create",
            {
                "name": "redekreis1",
                "meeting_id": 1,
                "read_group_ids": [1, 2],
                "write_group_ids": [anonymous_group],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Anonymous group is not allowed in write_group_ids.",
            response.json["message"],
        )
