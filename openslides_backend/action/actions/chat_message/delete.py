from typing import Any

from ....models.models import ChatMessage
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("chat_message.delete")
class ChatMessageDelete(DeleteAction):
    """
    Action to delet a chat message.
    """

    model = ChatMessage()
    schema = DefaultSchema(ChatMessage()).get_delete_schema()

    def check_permissions(self, instance: dict[str, Any]) -> None:
        chat_message = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["meeting_user_id", "meeting_id"],
            lock_result=False,
        )
        meeting_user = self.datastore.get(
            fqid_from_collection_and_id(
                "meeting_user", chat_message["meeting_user_id"]
            ),
            ["user_id"],
            lock_result=False,
        )
        if meeting_user.get("user_id") != self.user_id and not has_perm(
            self.datastore,
            self.user_id,
            Permissions.Chat.CAN_MANAGE,
            chat_message["meeting_id"],
        ):
            raise PermissionDenied(
                "You are not allowed to perform action chat_message.delete"
            )
