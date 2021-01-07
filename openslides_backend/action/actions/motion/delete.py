from ....models.models import Motion
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion.delete")
class MotionDelete(DeleteAction):
    """
    Action to delete motions.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_delete_schema()
