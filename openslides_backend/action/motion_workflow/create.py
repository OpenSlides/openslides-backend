from typing import Any, Dict, Type

from ...models.motion_workflow import MotionWorkflow
from ..action import register_action
from ..base import Action
from ..create_action_with_dependencies import CreateActionWithDependencies
from ..default_schema import DefaultSchema
from ..motion_state.create_update_delete import MotionStateActionSet

MOTION_STATE_DEFAULT_NAME = "default"


@register_action("motion_workflow.create")
class MotionWorkflowCreateAction(CreateActionWithDependencies):
    """
    Action to create a motion workflow.
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_create_schema(
        properties=["name", "meeting_id"], required_properties=["name", "meeting_id"],
    )
    dependencies = [MotionStateActionSet.get_action("create")]

    def get_dependent_action_payload(
        self, element: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> Dict[str, Any]:
        return {
            "name": MOTION_STATE_DEFAULT_NAME,
            "workflow_id": element["new_id"],
        }
