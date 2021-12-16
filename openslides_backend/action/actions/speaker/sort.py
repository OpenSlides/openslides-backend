from ....models.models import ListOfSpeakers, Speaker
from ....permissions.permissions import Permissions
from ....shared.filters import And, FilterOperator
from ...generics.update import UpdateAction
from ...mixins.linear_sort_mixin import LinearSortMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("speaker.sort")
class SpeakerSort(LinearSortMixin, SingularActionMixin, UpdateAction):
    """
    Action to sort speakers.
    """

    model = Speaker()
    schema = DefaultSchema(Speaker()).get_linear_sort_schema(
        "speaker_ids",
        "list_of_speakers_id",
    )
    permission = Permissions.ListOfSpeakers.CAN_MANAGE
    permission_model = ListOfSpeakers()
    permission_id = "list_of_speakers_id"

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))

        filter = And(
            FilterOperator("list_of_speakers_id", "=", instance["list_of_speakers_id"]),
            FilterOperator("begin_time", "=", None),
        )

        yield from self.sort_linear(
            nodes=instance["speaker_ids"],
            filter=filter,
        )
