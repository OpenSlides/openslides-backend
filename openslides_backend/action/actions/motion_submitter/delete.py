from ....models.models import MotionSubmitter
from ....permissions.permissions import Permissions
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_submitter.delete")
class MotionSubmitterDeleteAction(DeleteAction):
    """
    Action to delete a motion submitter.
    """

    model = MotionSubmitter()
    schema = DefaultSchema(MotionSubmitter()).get_delete_schema()
    history_information = "Submitters changed"
    permission = Permissions.Motion.CAN_MANAGE_METADATA
