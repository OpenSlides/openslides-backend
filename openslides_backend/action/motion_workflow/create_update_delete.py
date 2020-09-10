from ...models.motion_workflow import MotionWorkflow
from ..action import register_action_set
from ..action_set import ActionSet
from ..default_schema import DefaultSchema


@register_action_set("motion_workflow")
class MotionWorkflowActionSet(ActionSet):
    """
    Actions to create, update and delete motion workflows.
    """

    model = MotionWorkflow()
    create_schema = DefaultSchema(MotionWorkflow()).get_create_schema(
        properties=["name", "meeting_id"], required_properties=["name", "meeting_id"],
    )
    update_schema = DefaultSchema(MotionWorkflow()).get_update_schema(
        properties=["name", "first_state_id"]
    )
    delete_schema = DefaultSchema(MotionWorkflow()).get_delete_schema()
