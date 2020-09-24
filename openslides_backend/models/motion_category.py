from ..shared.patterns import Collection
from . import fields
from .base import Model


class MotionCategory(Model):
    """
    Model for motion category.

    Reverse fields:
    - child_ids: (motion_category/parent_id)[]
    - motion_ids: (motion/category_id)[]
    """

    collection = Collection("motion_category")
    verbose_name = "motion_category"

    id = fields.IdField(description="The id of this motion category.")
    meeting_id = fields.RequiredForeignKeyField(
        description="The id of the meeting of this motion_category.",
        to=Collection("meeting"),
        related_name="motion_category_ids",
    )
    name = fields.RequiredCharField(
        description="The name of this motion category.", maxLength=255
    )
    prefix = fields.RequiredCharField(
        description="The prefix of this motion category.", maxLength=32
    )
    weight = fields.IntegerField(description="The weight of this motion category")
    # TODO calculate the "level" field. (level: number;)
    #
    parent_id = fields.ForeignKeyField(
        description="The parent of a motion_category",
        to=Collection("motion_category"),
        related_name="child_ids",
    )
