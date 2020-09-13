from ..shared.patterns import Collection
from . import fields
from .base import Model


class MotionBlock(Model):
    """
    Model for motion block.

    There are the following reverse relation fields:
        motion_ids: (motion/block_id)[];
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
    agenda_item_id = fields.OneToOneField(
        description="The agenda item id of this motion block.",
        to=Collection("agenda_item"),
        related_name="content_object_id",
        generic_relation=True,
    )
    list_of_speakers_id = fields.OneToOneField(
        description="The list of speakers id of this motion block.",
        to=Collection("list_of_speakers"),
        related_name="content_object_id",
        generic_relation=True,
    )

    # TODO
    # projection_ids: (projection/element_id)[];
    # current_projector_ids: (projector/current_element_ids)[];
