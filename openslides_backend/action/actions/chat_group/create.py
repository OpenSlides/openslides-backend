from typing import Any, Dict

from ....models.models import ChatGroup
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("chat_group.create")
class ChatGroupCreate(CreateAction):
    """
    Action to create a chat group.
    """

    model = ChatGroup()
    schema = DefaultSchema(ChatGroup()).get_create_schema(
        required_properties=["name", "meeting_id"],
        optional_properties=["read_group_ids", "write_group_ids"],
    )
    permission = Permissions.Chat.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
            ["enable_chat"],
        )

        # if chat is not enabled raise error
        if not meeting.get("enable_chat"):
            raise ActionException("Chat is not enabled.")

        instance["weight"] = self.get_weight(instance["meeting_id"])
        return instance

    def get_weight(self, meeting_id: int) -> int:
        filter_ = FilterOperator("meeting_id", "=", meeting_id)
        maximum = self.datastore.max(Collection("chat_group"), filter_, "weight", "int")
        if maximum is None:
            return 1
        return maximum + 1
