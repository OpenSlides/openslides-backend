from ...models.models import MotionWorkflow
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import UpdateAction


@register_action("motion_workflow.update")
class MotionWorkflowUpdateAction(UpdateAction):
    """
    Action to update a motion workflow.
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_update_schema(
        properties=["name", "first_state_id"]
    )
