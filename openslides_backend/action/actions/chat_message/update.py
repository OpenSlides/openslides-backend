from typing import Any

from ....models.models import ChatMessage
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("chat_message.update")
class ChatMessageUpdate(UpdateAction):
    """
    Action to update a chat message.
    """

    model = ChatMessage()
    schema = DefaultSchema(ChatMessage()).get_update_schema(
        optional_properties=["content"],
    )

    def check_permissions(self, instance: dict[str, Any]) -> None:
        chat_message = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["meeting_user_id"],
            lock_result=False,
        )
        meeting_user = self.datastore.get(
            fqid_from_collection_and_id(
                "meeting_user", chat_message["meeting_user_id"]
            ),
            ["user_id"],
            lock_result=False,
        )
        if meeting_user.get("user_id") != self.user_id:
            raise PermissionDenied("You must be creator of a chat message to edit it.")
