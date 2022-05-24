from ....models.models import ChatGroup
from ....permissions.permissions import Permissions
from ....shared.patterns import to_fqid
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..chat_message.delete import ChatMessageDelete
from .mixins import ChatEnabledMixin


@register_action("chat_group.clear")
class ChatGroupClear(ChatEnabledMixin, UpdateAction):
    """
    Action to clear a chat group.
    """

    model = ChatGroup()
    schema = DefaultSchema(ChatGroup()).get_update_schema()
    permission = Permissions.Chat.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        delete_action_data = []
        for instance in action_data:
            chat_group = self.datastore.get(
                to_fqid(self.model.collection, instance["id"]),
                ["chat_message_ids"],
            )
            for id_ in chat_group.get("chat_message_ids", []):
                delete_action_data.append({"id": id_})
        self.execute_other_action(ChatMessageDelete, delete_action_data)
        return []
