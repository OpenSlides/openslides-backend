from ...models.models import Motion
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import DeleteAction


@register_action("motion.delete")
class MotionDelete(DeleteAction):
    """
    Action to delete motions.
    """

    # TODO: Allow deleting for managers and for submitters (but only in some states)

    model = Motion()
    schema = DefaultSchema(Motion()).get_delete_schema()
