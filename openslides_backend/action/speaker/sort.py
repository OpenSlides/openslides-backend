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
        "speaker_ids", "list_of_speakers_id",
    )

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        # payload is an array with exactly one item
        return self.sort_linear(
            nodes=payload[0]["speaker_ids"],
            filter_id=payload[0]["list_of_speakers_id"],
            filter_str="list_of_speakers_id",
        )
