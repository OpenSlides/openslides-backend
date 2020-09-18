from ..shared.patterns import Collection
from . import fields
from .base import Model


class Topic(Model):
    """
    Model for simple topics that can be shown in agenda.

    There are the following reverse relation fields: None
    """

    collection = Collection("topic")
    verbose_name = "topic"

    id = fields.IdField(description="The id of this topic.")
    meeting_id = fields.RequiredForeignKeyField(
        description="The id of the meeting of this topic.",
        to=Collection("meeting"),
        related_name="topic_ids",
    )
    title = fields.RequiredCharField(description="The title or headline of this topic.")
    text = fields.TextField(description="The HTML formatted text of this topic.")
    attachment_ids = fields.ManyToManyArrayField(
        description="The attachments that should be related with this topic.",
        to=Collection("mediafile"),
        related_name="attachment_ids",
        generic_relation=True,
    )
    tag_ids = fields.ManyToManyArrayField(
        description="The tags that should be related with this topic.",
        to=Collection("tag"),
        related_name="tagged_ids",
        generic_relation=True,
    )
    agenda_item_id = fields.OneToOneField(
        description="The id of the agenda item.",
        to=Collection("agenda_item"),
        related_name="content_object_id",
        generic_relation=True,
        delete_protection=True,
    )
    list_of_speakers_id = fields.OneToOneField(
        description="The list of speakers id of this motion block.",
        to=Collection("list_of_speakers"),
        related_name="content_object_id",
        generic_relation=True,
        delete_protection=True,
    )
