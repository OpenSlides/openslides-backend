from ....models.models import ChatGroup
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...mixins.linear_sort_mixin import LinearSortMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import ChatEnabledMixin


@register_action("chat_group.sort")
class ChatGroupSort(
    ChatEnabledMixin, LinearSortMixin, SingularActionMixin, UpdateAction
):
    """
    Action to sort chat groups.
    """

    model = ChatGroup()
    schema = DefaultSchema(ChatGroup()).get_linear_sort_schema(
        "chat_group_ids",
        "meeting_id",
    )
    permission = Permissions.Chat.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        yield from self.sort_linear(
            nodes=instance["chat_group_ids"],
            filter_id=instance["meeting_id"],
            filter_str="meeting_id",
        )
