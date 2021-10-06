from ....models.models import MotionState
from ....permissions.permissions import Permissions
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_state.delete")
class MotionStateDeleteAction(DeleteAction):
    """
    Action to delete a motion state.
    """

    model = MotionState()
    schema = DefaultSchema(MotionState()).get_delete_schema()
    permission = Permissions.Motion.CAN_MANAGE
