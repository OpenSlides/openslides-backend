from ...models.models import MotionSubmitter
from ..default_schema import DefaultSchema
from ..generics import DeleteAction
from ..register import register_action


@register_action("motion_submitter.delete")
class MotionSubmitterDeleteAction(DeleteAction):
    """
    Action to delete a motion submitter.
    """

    model = MotionSubmitter()
    schema = DefaultSchema(MotionSubmitter()).get_delete_schema()
