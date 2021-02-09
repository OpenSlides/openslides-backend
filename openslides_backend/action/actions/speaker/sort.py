from typing import Optional

from ....models.models import Speaker
from ....shared.filters import And, Filter, FilterOperator
from ...generics.update import UpdateAction
from ...mixins.linear_sort_mixin import LinearSortMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionPayload


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

    def get_updated_instances(self, payload: ActionPayload) -> ActionPayload:
        filter: Optional[Filter] = None
        payload = super().get_updated_instances(payload)
        # Payload is an iterable with exactly one item
        instance = next(iter(payload))
        if not filter:
            filter = And(
                FilterOperator(
                    "list_of_speakers_id", "=", instance["list_of_speakers_id"]
                ),
                FilterOperator("end_time", "=", None),
            )

        yield from self.sort_linear(
            nodes=instance["speaker_ids"], filter_id=0, filter_str="", filter=filter
        )
