from typing import Any

from ....models.models import ChatGroup
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...mixins.forbid_anonymous_group_mixin import ForbidAnonymousGroupMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import ChatEnabledMixin


@register_action("chat_group.update")
class ChatGroupUpdate(
    ChatEnabledMixin, UpdateAction, ForbidAnonymousGroupMixin
):
    """
    Action to update a chat group.
    """

    model = ChatGroup()
    schema = DefaultSchema(ChatGroup()).get_update_schema(
        optional_properties=["name", "read_group_ids", "write_group_ids"],
    )
    permission = Permissions.Chat.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        self.check_anonymous_not_in_list_fields(instance, ["write_group_ids"])
        return instance
