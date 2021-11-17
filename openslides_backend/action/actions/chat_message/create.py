from time import time
from typing import Any, Dict

from ....models.models import ChatMessage
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("chat_message.create")
class ChatMessageCreate(CreateAction):
    """
    Action to create a chat message.
    """

    model = ChatMessage()
    schema = DefaultSchema(ChatMessage()).get_create_schema(
        required_properties=["chat_group_id", "content"],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance["user_id"] = self.user_id
        instance["meeting_id"] = self.get_meeting_id(instance)
        instance["created"] = round(time())
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        chat_group = self.datastore.get(
            FullQualifiedId(Collection("chat_group"), instance["chat_group_id"]),
            ["meeting_id", "write_group_ids"],
        )
        write_group_set = set(chat_group.get("write_group_ids", []))
        meeting_id = chat_group["meeting_id"]
        user = self.datastore.get(
            FullQualifiedId(Collection("user"), self.user_id),
            [f"group_${meeting_id}_ids"],
        )
        user_group_set = set(user.get(f"group_${meeting_id}_ids", []))
        if not (write_group_set & user_group_set):
            raise PermissionDenied("You are not allowed to write in this chat group.")

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        chat_group = self.datastore.get(
            FullQualifiedId(Collection("chat_group"), instance["chat_group_id"]),
            ["meeting_id"],
        )
        return chat_group["meeting_id"]
