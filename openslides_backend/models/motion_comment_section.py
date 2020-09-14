from ..shared.patterns import Collection
from . import fields
from .base import Model


class MotionCommentSection(Model):
    """
    Model for motion comment section.

    There are the following reverse relation fields:
        comment_ids: (motion_comment/section_id)[];
    """

    collection = Collection("motion_comment_section")
    verbose_name = "motion_comment_section"

    id = fields.IdField(description="The id of this motion comment section.")
    meeting_id = fields.RequiredForeignKeyField(
        description="The id of the meeting of this motion comment section.",
        to=Collection("meeting"),
        related_name="motion_comment_section_ids",
    )
    name = fields.RequiredCharField(
        description="The name of this motion comment section."
    )
    weight = fields.IntegerField(
        description="The weight of this motion comment section."
    )
    read_group_ids = fields.ManyToManyArrayField(
        description="The read_group_ids of this motion comment section",
        to=Collection("group"),
        related_name="read_comment_section_ids",
    )
    write_group_ids = fields.ManyToManyArrayField(
        description="The write_group_ids of this motion comment section",
        to=Collection("group"),
        related_name="write_comment_section_ids",
    )
