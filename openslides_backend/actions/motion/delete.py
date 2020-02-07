import fastjsonschema  # type: ignore

from ...models.motion import Motion
from ...shared.permissions.motion import MOTION_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..generics import DeleteAction

delete_motion_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Delete motions schema",
        "description": "An array of motions to be deleted.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {"id": Motion().get_schema("id")},
            "required": ["id"],
            "additionalProperties": False,
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("motion.delete")
class MotionDelete(DeleteAction):
    """
    Action to delete motions.
    """

    # TODO: Allow deleting for managers and for submitters (but only in some states)

    model = Motion()
    schema = delete_motion_schema
    permissions = [MOTION_CAN_MANAGE]
