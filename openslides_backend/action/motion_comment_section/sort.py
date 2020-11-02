from ...models.models import MotionCommentSection
from ..base import Action, ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..register import register_action
from ..sort_generic import LinearSortMixin


@register_action("motion_comment_section.sort")
class MotionCommentSectionSort(LinearSortMixin, Action):
    """
    Action to sort motion comment sections.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_linear_sort_schema(
        "motion_comment_section_ids",
        "meeting_id",
    )

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        # Payload is an iterable with exactly one item
        instance = next(iter(payload))
        return self.sort_linear(
            nodes=instance["motion_comment_section_ids"],
            filter_id=instance["meeting_id"],
            filter_str="meeting_id",
        )
