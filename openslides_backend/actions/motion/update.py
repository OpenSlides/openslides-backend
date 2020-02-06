import fastjsonschema  # type: ignore

from ...models.motion import Motion
from ...shared.permissions.motion import MOTION_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..generics import UpdateAction

update_motion_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Update motions schema",
        "description": "An array of motions to be updated.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": Motion().get_schema("id"),
                "title": Motion().get_schema("title"),
                "motion_category_id": Motion().get_schema("motion_category_id"),
            },
            "required": ["id"],
            "additionalProperties": False,
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("motion.update")
class MotionUpdate(UpdateAction):
    """
    Action to update motions.
    """

    model = Motion()
    schema = update_motion_schema
    manage_permission = MOTION_CAN_MANAGE
