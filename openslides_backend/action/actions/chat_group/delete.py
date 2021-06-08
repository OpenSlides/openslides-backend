from typing import Any, Dict

from ....models.models import ChatGroup
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("chat_group.delete")
class ChatGroupDelete(DeleteAction):
    """
    Action to delete a chat group.
    """

    model = ChatGroup()
    schema = DefaultSchema(ChatGroup()).get_delete_schema()
    permission = Permissions.Chat.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        chat_group = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]), ["meeting_id"]
        )
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), chat_group["meeting_id"]),
            ["enable_chat"],
        )
        if not meeting.get("enable_chat"):
            raise ActionException("Chat is not enabled.")
        return instance
