from ....models.models import MotionCommentSection
from ...generics.update import UpdateAction
from ...mixins.linear_sort_mixin import LinearSortMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("motion_comment_section.sort")
class MotionCommentSectionSort(LinearSortMixin, SingularActionMixin, UpdateAction):
    """
    Action to sort motion comment sections.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_linear_sort_schema(
        "motion_comment_section_ids",
        "meeting_id",
    )

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        yield from self.sort_linear(
            nodes=instance["motion_comment_section_ids"],
            filter_id=instance["meeting_id"],
            filter_str="meeting_id",
        )
