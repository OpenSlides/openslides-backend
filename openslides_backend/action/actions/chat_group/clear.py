from ....models.models import ChatGroup
from ....permissions.permissions import Permissions
from ....shared.patterns import FullQualifiedId
from ....shared.schema import required_id_schema
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
    schema = DefaultSchema(ChatGroup()).get_default_schema(
        title="Schema for clear a chat group.",
        additional_required_fields={"chat_group_id": required_id_schema},
    )
    permission = Permissions.Chat.CAN_MANAGE
    permission_id = "chat_group_id"

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            chat_group = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["chat_group_id"]),
                ["chat_message_ids"],
            )
            delete_action_data = []
            for id_ in chat_group.get("chat_message_ids", []):
                delete_action_data.append({"id": id_})
            self.execute_other_action(ChatMessageDelete, delete_action_data)
        return []
