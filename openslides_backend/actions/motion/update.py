import time

import fastjsonschema  # type: ignore

from ...models.motion import Motion
from ...shared.permissions.motion import MOTION_CAN_MANAGE, MOTION_CAN_MANAGE_METADATA
from ...shared.schema import schema_version
from ..actions import register_action
from ..actions_interface import Payload
from ..base import DataSet
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
                "motion_statute_paragraph_id": Motion().get_schema(
                    "motion_statute_paragraph_id"
                ),
                # TODO identifier, modified_final_version, reason, text, amendmend_paragraphs, parent_id, mediafile_attachment
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
    permissions = [MOTION_CAN_MANAGE]

    def prepare_dataset(self, payload: Payload) -> DataSet:
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
            "properties": {
                "id": Motion().get_schema("id"),
                "motion_category_id": Motion().get_schema("motion_category_id"),
                "motion_block_id": Motion().get_schema("motion_block_id"),
                "origin_id": Motion().get_schema("origin_id"),
                "state_id": Motion().get_schema("state_id"),
                "state_extension": Motion().get_schema("state_extension"),
                "recommendation_id": Motion().get_schema("recommendation_id"),
                "recommendation_extension": Motion().get_schema(
                    "recommendation_extension"
                ),
                "supporter_ids": Motion().get_schema("supporter_ids"),
                "tag_ids": Motion().get_schema("tag_ids"),
                # TODO submitters
            },
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

    def prepare_dataset(self, payload: Payload) -> DataSet:
        for instance in payload:
            instance["last_modified"] = round(time.time())
        return super().prepare_dataset(payload)


# TODO: Cateogry weight is extra

# TODO: Sort (sort_weight, sort_parent_id)

# TODO: comments

# TODO: create poll
