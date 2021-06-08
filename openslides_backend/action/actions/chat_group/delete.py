from ....models.models import ChatGroup
from ....permissions.permissions import Permissions
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import ChatEnabledMixin


@register_action("chat_group.delete")
class ChatGroupDelete(ChatEnabledMixin, DeleteAction):
    """
    Action to delete a chat group.
    """

    model = ChatGroup()
    schema = DefaultSchema(ChatGroup()).get_delete_schema()
    permission = Permissions.Chat.CAN_MANAGE
