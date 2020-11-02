from ...models.models import Speaker
from ..base import Action, ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..register import register_action
from ..sort_generic import LinearSortMixin


@register_action("speaker.sort")
class SpeakerSort(LinearSortMixin, Action):
    """
    Action to sort speakers.
    """

    model = Speaker()
    schema = DefaultSchema(Speaker()).get_linear_sort_schema(
        "speaker_ids",
        "list_of_speakers_id",
    )

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        # Payload is an iterable with exactly one item
        instance = next(iter(payload))
        return self.sort_linear(
            nodes=instance["speaker_ids"],
            filter_id=instance["list_of_speakers_id"],
            filter_str="list_of_speakers_id",
        )
