from time import time
from typing import Any, Dict
from openslides_backend.shared.filters import And, FilterOperator

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
from ..meeting_user.helper import MeetingUserHelper


@register_action("chat_message.create")
class ChatMessageCreate(MeetingUserHelper, CreateActionWithInferredMeeting):
    """
    Action to create a chat message.
    """

    model = ChatMessage()
    schema = DefaultSchema(ChatMessage()).get_create_schema(
        required_properties=["chat_group_id", "content"],
    )
    relation_field_for_meeting = "chat_group_id"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        instance["meeting_user_id"] = self.create_or_get_meeting_user(
            instance["meeting_id"], self.user_id
        )
        instance["created"] = round(time())
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        chat_group = self.datastore.get(
            fqid_from_collection_and_id("chat_group", instance["chat_group_id"]),
            ["meeting_id", "write_group_ids"],
            lock_result=False,
        )
        write_group_set = set(chat_group.get("write_group_ids", []))
        meeting_id = chat_group["meeting_id"]
        filter_result = self.datastore.filter(
            "meeting_user",
            And(
                FilterOperator("meeting_id", "=", meeting_id),
                FilterOperator("user_id", "=", self.user_id),
            ),
            ["group_ids"],
            lock_result=False,
        )
        if len(filter_result) == 1:
            meeting_user = list(filter_result.values())[0]
            user_group_set = set(meeting_user.get("group_ids", ()))
        else:
            user_group_set = set()
        if not (
            (write_group_set & user_group_set)
            or has_perm(
                self.datastore, self.user_id, Permissions.Chat.CAN_MANAGE, meeting_id
            )
        ):
            raise PermissionDenied("You are not allowed to write in this chat group.")
