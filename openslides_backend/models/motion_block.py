from ..shared.patterns import Collection
from . import fields
from .base import Model


class MotionBlock(Model):
    """
    Model for motion block.

    Reverse fields:
    - motion_ids
    - projection_ids
    - current_projection_ids
    """

    collection = Collection("motion_block")
    verbose_name = "motion_block"

    id = fields.IdField(description="The id of this motion block.")
    meeting_id = fields.RequiredForeignKeyField(
        description="The id of the meeting of this motion block.",
        to=Collection("meeting"),
        related_name="motion_block_ids",
    )
    title = fields.RequiredCharField(description="The title of this motion block.")
    internal = fields.BooleanField(description="If the motion block is internal.")
    list_of_speakers_id = fields.ForeignKeyField(
        description="The list of speakers id of this motion block.",
        to=Collection("list_of_speakers"),
        related_name="content_object_id",
    )
    # TODO related_name should be "content_object_id"
    agenda_item_id = fields.ForeignKeyField(
        description="The agenda item id of this motion block.",
        to=Collection("agenda_item"),
        related_name="agenda_item_id",
    )
