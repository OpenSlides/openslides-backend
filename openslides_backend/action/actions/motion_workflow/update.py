from ....action.util.typing import ActionData, ActionResults
from ....models.models import MotionWorkflow
from ....permissions.permissions import Permissions
from ...ddaction import DDAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_workflow.update")
class MotionWorkflowUpdateAction(DDAction):
    """
    Action to update a motion workflow.
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_update_schema(
        optional_properties=["name", "first_state_id"]
    )
    permission = Permissions.Motion.CAN_MANAGE

    def write_instances(self, action_data: ActionData) -> ActionResults | None:
        return list(
            self.database.update_models(
                self.model.collection,
                list(action_data),
            )
        )
