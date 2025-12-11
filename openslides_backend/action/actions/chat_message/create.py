from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from ....models.models import ChatMessage
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..meeting_user.helper_mixin import MeetingUserHelperMixin


@register_action("chat_message.create")
class ChatMessageCreate(MeetingUserHelperMixin, CreateActionWithInferredMeeting):
    """
    Action to create a chat message.
    """

    model = ChatMessage()
    schema = DefaultSchema(ChatMessage()).get_create_schema(
        required_properties=["chat_group_id", "content"],
    )
    relation_field_for_meeting = "chat_group_id"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        instance["meeting_user_id"] = self.create_or_get_meeting_user(
            instance["meeting_id"], self.user_id
        )
        instance["created"] = datetime.now(ZoneInfo("UTC"))
        return instance

    def check_permissions(self, instance: dict[str, Any]) -> None:
        chat_group = self.datastore.get(
            fqid_from_collection_and_id("chat_group", instance["chat_group_id"]),
            ["meeting_id", "write_group_ids"],
            lock_result=False,
        )
        write_group_set = set(chat_group.get("write_group_ids", []))
        meeting_id = chat_group["meeting_id"]
        user_group_set = set(
            self.get_groups_from_meeting_user(meeting_id, self.user_id)
        )
        if not (
            (write_group_set & user_group_set)
            or has_perm(
                self.datastore, self.user_id, Permissions.Chat.CAN_MANAGE, meeting_id
            )
        ):
            raise PermissionDenied("You are not allowed to write in this chat group.")
