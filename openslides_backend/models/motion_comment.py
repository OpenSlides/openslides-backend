from ..shared.patterns import Collection
from . import fields
from .base import Model


class MotionComment(Model):
    """
    Model for motion comments-

    There are the following reverse relation fields:
    -/-
    """

    collection = Collection("motion_comment")
    verbose_name = "motion_comment"

    id = fields.IdField(description="The id of this motion comment.")
    comment = fields.HtmlField(
        description="The comment of this motion comment.",
        allowed_tags=fields.ALLOWED_HTML_TAGS_STRICT,
    )
    motion_id = fields.RequiredForeignKeyField(
        description="The id of the motion of this motion comment.",
        to=Collection("motion"),
        related_name="comment_ids",
    )
    section_id = fields.RequiredForeignKeyField(
        description="The id of the section of this motion comment.",
        to=Collection("motion_comment_section"),
        related_name="comment_ids",
    )
