from typing import Any, Dict, List, Type

from ....models.models import MotionWorkflow
from ...action import Action
from ...mixins.create_action_with_dependencies import CreateActionWithDependencies
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..motion_state.create_update_delete import MotionStateActionSet

MOTION_STATE_DEFAULT_NAME = "default"


@register_action("motion_workflow.create")
class MotionWorkflowCreateAction(CreateActionWithDependencies):
    """
    Action to create a motion workflow.
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_create_schema(["name", "meeting_id"])
    dependencies = [MotionStateActionSet.get_action("create")]

    def get_dependent_action_payload(
        self, instance: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> List[Dict[str, Any]]:
        return [
            {
                "name": MOTION_STATE_DEFAULT_NAME,
                "workflow_id": instance["id"],
                "first_state_of_workflow_id": instance["id"],
            }
        ]
