import time

import fastjsonschema  # type: ignore

from ...models.motion import Motion
from ...shared.permissions.motion import MOTION_CAN_MANAGE, MOTION_CAN_MANAGE_METADATA
from ...shared.schema import schema_version
from ..actions import register_action
from ..base import ActionPayload, DataSet
from ..generics import UpdateAction

update_motion_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Update motions schema",
        "description": "An array of motions to be updated.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": Motion().get_properties(
                "id", "title", "motion_statute_paragraph_id",
            ),  # TODO identifier, modified_final_version, reason, text, amendmend_paragraphs, parent_id, mediafile_attachment
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
    permissions = [MOTION_CAN_MANAGE]

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        if not isinstance(payload, list):
            raise TypeError("ActionPayload for this action must be a list.")
        for instance in payload:
            instance["last_modified"] = round(time.time())
        return super().prepare_dataset(payload)


update_motion_metadata_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Update motions metadata schema",
        "description": "An array of motions to be updated.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": Motion().get_properties(
                "id",
                "motion_category_id",
                "motion_block_id",
                "origin_id",
                "state_id",
                "state_extension",
                "recommendation_id",
                "recommendation_extension",
                "supporter_ids",
                "tag_ids",
            ),  # TODO submitters
            "required": ["id"],
            "additionalProperties": False,
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("motion.update_metadata")
class MotionUpdateMetadata(UpdateAction):
    """
    Action to update motion metadata.
    """

    model = Motion()
    schema = update_motion_metadata_schema
    permissions = [MOTION_CAN_MANAGE, MOTION_CAN_MANAGE_METADATA]

    # TODO: Check removal of supporters and maybe remove them in some state.

    # TODO: Enable set_state without any given state to reset to first state

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        if not isinstance(payload, list):
            raise TypeError("ActionPayload for this action must be a list.")
        for instance in payload:
            instance["last_modified"] = round(time.time())
        return super().prepare_dataset(payload)


# TODO: Support and unsupport

# TODO: follow_recommendation

# TODO: Cateogry weight is extra

# TODO: comments

# TODO: create poll
