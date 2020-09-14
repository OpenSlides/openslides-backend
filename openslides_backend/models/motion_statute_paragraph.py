from ..shared.patterns import Collection
from . import fields
from .base import Model


class MotionStatuteParagraph(Model):
    """
    Model for motion statute paragraph.

    Reverse fields:
        motion_ids: (motion/statute_paragraph_id)[];
    """

    collection = Collection("motion_statute_paragraph")
    verbose_name = "motion_statute_paragraph"

    id = fields.IdField(description="The id of this motion statute paragraph.")
    meeting_id = fields.RequiredForeignKeyField(
        description="The id of the meeting of this motion statute paragraph.",
        to=Collection("meeting"),
        related_name="motion_statute_paragraph_ids",
    )
    title = fields.RequiredCharField(
        description="The title of this motion statute paragraph."
    )
    text = fields.TextField(description="The text of this statute paragraph.")
    weight = fields.IntegerField(
        description="The weight of this motion statute paragraph."
    )
