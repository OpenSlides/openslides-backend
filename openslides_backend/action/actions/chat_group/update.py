from ....models.models import ChatGroup
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import ChatEnabledMixin


@register_action("chat_group.update")
class ChatGroupUpdate(ChatEnabledMixin, UpdateAction):
    """
    Action to update a projector message.
    """

    model = ChatGroup()
    schema = DefaultSchema(ChatGroup()).get_update_schema(
        optional_properties=["name", "read_group_ids", "write_group_ids"],
    )
    permission = Permissions.Chat.CAN_MANAGE
