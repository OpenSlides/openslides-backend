from ....models.models import Speaker
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
        self.assert_singular_payload(payload)
        # Payload is an iterable with exactly one item
        instance = next(iter(payload))
        yield from self.sort_linear(
            nodes=instance["speaker_ids"],
            filter_id=instance["list_of_speakers_id"],
            filter_str="list_of_speakers_id",
        )
