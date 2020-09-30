from ...models.models import MotionCommentSection
from ..action import register_action
from ..base import Action, ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..sort_generic import LinearSortMixin


@register_action("motion_comment_section.sort")
class MotionCommentSectionSort(LinearSortMixin, Action):
    """
    Action to sort motion comment sections.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_linear_sort_schema(
        "motion_comment_section_ids"
    )

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        if not isinstance(payload, dict):
            raise TypeError("ActionPayload for this action must be a dictionary.")
        return self.sort_linear(
            nodes=payload["motion_comment_section_ids"],
            meeting_id=payload["meeting_id"],
        )
