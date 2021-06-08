from ....models.models import ChatGroup
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...mixins.linear_sort_mixin import LinearSortMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("chat_group.sort")
class ChatGroupSort(LinearSortMixin, SingularActionMixin, UpdateAction):
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
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
            ["enable_chat"],
        )

        # if chat is not enabled raise error
        if not meeting.get("enable_chat"):
            raise ActionException("Chat is not enabled.")

        yield from self.sort_linear(
            nodes=instance["chat_group_ids"],
            filter_id=instance["meeting_id"],
            filter_str="meeting_id",
        )
