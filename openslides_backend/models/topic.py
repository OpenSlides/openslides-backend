from ..shared.patterns import Collection
from . import fields
from .base import Model


class Topic(Model):
    """
    Model for simple topics that can be shown in agenda.
    """

    collection = Collection("topic")
    verbose_name = "topic"

    id = fields.IdField(description="The id of this topic.")
    meeting_id = fields.ForeignKeyField(
        description="The id of the meeting of this topic.",
        to=Collection("meeting"),
        related_name="topic_ids",
    )
    title = fields.RequiredCharField(description="The title or headline of this topic.")
    text = fields.TextField(description="The HTML formatted text of this topic.")
    mediafile_attachment_ids = fields.ManyToManyArrayField(
        description="The attachments that should be referenced with this topic.",
        to=Collection("mediafile_attachment"),
        related_name="topic_ids",
    )
