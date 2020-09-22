from ...models.motion_workflow import MotionWorkflow
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import CreateAction


@register_action("motion_workflow.create")
class MotionWorkflowCreateAction(CreateAction):
    """
    Action to create a motion workflow.
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_create_schema(
        properties=["name", "meeting_id"], required_properties=["name", "meeting_id"],
    )
