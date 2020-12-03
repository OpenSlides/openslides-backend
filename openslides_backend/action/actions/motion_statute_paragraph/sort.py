from ....models.models import MotionStatuteParagraph
from ...generics.update import UpdateAction
from ...mixins.linear_sort_mixin import LinearSortMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionPayload


@register_action("motion_statute_paragraph.sort")
class MotionStatueParagraphSort(LinearSortMixin, SingularActionMixin, UpdateAction):
    """
    Action to sort motion statue paragraph.
    """

    model = MotionStatuteParagraph()
    schema = DefaultSchema(MotionStatuteParagraph()).get_linear_sort_schema(
        "statute_paragraph_ids",
        "meeting_id",
    )

    def get_updated_instances(self, payload: ActionPayload) -> ActionPayload:
        self.assert_singular_payload(payload)
        # Payload is an iterable with exactly one item
        instance = next(iter(payload))
        yield from self.sort_linear(
            nodes=instance["statute_paragraph_ids"],
            filter_id=instance["meeting_id"],
            filter_str="meeting_id",
        )
