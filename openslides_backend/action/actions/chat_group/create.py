from typing import Any, Dict

from ....models.models import ChatGroup
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import Collection
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import ChatEnabledMixin


@register_action("chat_group.create")
class ChatGroupCreate(ChatEnabledMixin, CreateAction):
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
        instance = super().update_instance(instance)
        self.check_name_unique(instance)
        instance["weight"] = self.get_weight(instance["meeting_id"])
        return instance

    def get_weight(self, meeting_id: int) -> int:
        filter_ = FilterOperator("meeting_id", "=", meeting_id)
        maximum = self.datastore.max(Collection("chat_group"), filter_, "weight", "int")
        if maximum is None:
            return 1
        return maximum + 1

    def check_name_unique(self, instance: Dict[str, Any]) -> None:
        name_exists = self.datastore.exists(
            self.model.collection,
            FilterOperator("name", "=", instance["name"]),
            lock_result=False,
        )
        if name_exists:
            raise ActionException("The name of a chat group must be unique.")
