from ..shared.patterns import Collection
from . import fields
from .base import Model


class Tag(Model):
    """
    Model for tags.

    There are the following reverse relation fields:
        tagged_ids: ({agenda_item,assignment,motion,topic}/tag_ids)[];
    """

    collection = Collection("tag")
    verbose_name = "tag"

    id = fields.IdField(description="The id of this tag.")
    name = fields.RequiredCharField(description="The name of this tag.")
    meeting_id = fields.RequiredForeignKeyField(
        description="The id of the meeting of this tag.",
        to=Collection("meeting"),
        related_name="tag_ids",
    )
