from ...models.motion import Motion
from ..action import register_action_set
from ..action_set import ActionSet
from ..default_schema import DefaultSchema
from .create import MotionCreate
from .delete import MotionDelete
from .update import MotionUpdate


@register_action_set("motion")
class MotionActionSet(ActionSet):
    """
    Actions to create, update and delete motion.
    """

    model = Motion()
    create_schema = DefaultSchema(Motion()).get_create_schema(
        properties=["title", "statute_paragraph_id"], required_properties=[],
    )
    update_schema = DefaultSchema(Motion()).get_update_schema(
        properties=["title", "statute_paragraph_id"]
    )
    delete_schema = DefaultSchema(Motion()).get_delete_schema()
    routes = {"create": MotionCreate, "update": MotionUpdate, "delete": MotionDelete}
