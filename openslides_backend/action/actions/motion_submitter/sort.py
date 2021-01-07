from ....models.models import MotionSubmitter
from ...generics.update import UpdateAction
from ...mixins.linear_sort_mixin import LinearSortMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionPayload


@register_action("motion_submitter.sort")
class MotionSubmitterSort(LinearSortMixin, SingularActionMixin, UpdateAction):
    """
    Action to sort motion comment sections.
    """

    model = MotionSubmitter()
    schema = DefaultSchema(MotionSubmitter()).get_linear_sort_schema(
        "motion_submitter_ids", "motion_id"
    )

    def get_updated_instances(self, payload: ActionPayload) -> ActionPayload:
        payload = super().get_updated_instances(payload)
        # Payload is an iterable with exactly one item
        instance = next(iter(payload))
        yield from self.sort_linear(
            nodes=instance["motion_submitter_ids"],
            filter_id=instance["motion_id"],
            filter_str="motion_id",
        )
