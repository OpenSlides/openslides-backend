from ...models.models import Motion
from ..default_schema import DefaultSchema
from ..generics import DeleteAction
from ..register import register_action


@register_action("motion.delete")
class MotionDelete(DeleteAction):
    """
    Action to delete motions.
    """

    # TODO: Allow deleting for managers and for submitters (but only in some states)

    model = Motion()
    schema = DefaultSchema(Motion()).get_delete_schema()
