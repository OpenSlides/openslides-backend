from typing import Any

from ....models.models import ChatGroup
from ....permissions.permissions import Permissions
from ...generics.create import CreateAction
from ...mixins.weight_mixin import WeightMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import ChatEnabledMixin, CheckUniqueNameMixin


@register_action("chat_group.create")
class ChatGroupCreate(
    WeightMixin, ChatEnabledMixin, CheckUniqueNameMixin, CreateAction
):
    """
    Action to create a chat group.
    """

    model = ChatGroup()
    schema = DefaultSchema(ChatGroup()).get_create_schema(
        required_properties=["name", "meeting_id"],
        optional_properties=["read_group_ids", "write_group_ids"],
    )
    permission = Permissions.Chat.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        self.check_name_unique(instance)
        instance["weight"] = self.get_weight(instance["meeting_id"])
        return instance
