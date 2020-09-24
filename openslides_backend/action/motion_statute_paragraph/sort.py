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
        "statute_paragraph_ids"
    )

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        if not isinstance(payload, dict):
            raise TypeError("ActionPayload for this action must be a dictionary.")
        return self.sort_linear(
            nodes=payload["statute_paragraph_ids"], meeting_id=payload["meeting_id"],
        )
