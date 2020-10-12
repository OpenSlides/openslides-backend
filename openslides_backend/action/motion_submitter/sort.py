from ...models.models import MotionSubmitter
from ..base import Action, ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..register import register_action
from ..sort_generic import LinearSortMixin


@register_action("motion_submitter.sort")
class MotionSubmitterSort(LinearSortMixin, Action):
    """
    Action to sort motion comment sections.
    """

    model = MotionSubmitter()
    schema = DefaultSchema(MotionSubmitter()).get_linear_sort_schema(
        "motion_submitter_ids", "motion_id"
    )

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        # payload is an array with exactly one item
        return self.sort_linear(
            nodes=payload[0]["motion_submitter_ids"],
            filter_id=payload[0]["motion_id"],
            filter_str="motion_id",
        )
