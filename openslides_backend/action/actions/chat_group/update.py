from typing import Any, Dict

from ....models.models import ChatGroup
from ....permissions.permissions import Permissions
from ....shared.patterns import FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import ChatEnabledMixin, CheckUniqueNameMixin


@register_action("chat_group.update")
class ChatGroupUpdate(ChatEnabledMixin, CheckUniqueNameMixin, UpdateAction):
    """
    Action to update a chat group.
    """

    model = ChatGroup()
    schema = DefaultSchema(ChatGroup()).get_update_schema(
        optional_properties=["name", "read_group_ids", "write_group_ids"],
    )
    permission = Permissions.Chat.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        if "name" in instance:
            chat_group = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["name"]
            )
            if instance["name"] != chat_group.get("name"):
                self.check_name_unique(instance)
        return instance
