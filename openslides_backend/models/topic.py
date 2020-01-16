from ..shared.patterns import Collection
from . import fields
from .base import Model


class Topic(Model):
    """
    Model for simple topics that can be shown in agenda.
    """

    collection = Collection("topic")

    # TODO: Make to and related_name in relation fields optional.

    id = fields.IdField(description="An integer. The id of the topic.")
    meeting_id = fields.ForeignKeyField(
        description="An integer. The id of the meeting of the topic.",
        to="meeting",
        related_name="topic_ids",
    )
    title = fields.RequiredCharField(
        description="A string. The title or headline of the topic."
    )
    text = fields.TextField(description="A string containing HTML formatted text.")
    mediafile_attachment_ids = fields.ManyToManyArrayField(
        description="An array of attachment ids that should be referenced with this topic.",
        to="mediafile_attachment",
        related_name="topic_ids",
    )
