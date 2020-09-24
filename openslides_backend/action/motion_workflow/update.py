from ...models.models import MotionWorkflow
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("motion_workflow.update")
class MotionWorkflowUpdateAction(UpdateAction):
    """
    Action to update a motion workflow.
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_update_schema(
        properties=["name", "first_state_id"]
    )
