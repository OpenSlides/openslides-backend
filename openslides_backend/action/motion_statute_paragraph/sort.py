from ...models.models import MotionStatuteParagraph
from ..base import Action, ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..register import register_action
from ..sort_generic import LinearSortMixin


@register_action("motion_statute_paragraph.sort")
class MotionStatueParagraphSort(LinearSortMixin, Action):
    """
    Action to sort motion statue paragraph.
    """

    model = MotionStatuteParagraph()
    schema = DefaultSchema(MotionStatuteParagraph()).get_linear_sort_schema(
        "statute_paragraph_ids", "meeting_id",
    )

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        # Payload is an iterable with exactly one item
        instance = next(iter(payload))
        return self.sort_linear(
            nodes=instance["statute_paragraph_ids"],
            filter_id=instance["meeting_id"],
            filter_str="meeting_id",
        )
