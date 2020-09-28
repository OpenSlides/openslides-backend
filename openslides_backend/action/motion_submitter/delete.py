from ...models.models import MotionSubmitter
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import DeleteAction


@register_action("motion_submitter.delete")
class MotionSubmitterDeleteAction(DeleteAction):
    """
    Action to delete a motion submitter.
    """

    model = MotionSubmitter()
    schema = DefaultSchema(MotionSubmitter()).get_delete_schema()
