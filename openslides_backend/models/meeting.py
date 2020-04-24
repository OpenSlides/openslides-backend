from ..shared.patterns import Collection
from . import fields
from .base import Model


class Meeting(Model):
    """
    Model for meetings.
    """

    collection = Collection("meeting")
    verbose_name = "meeting"

    id = fields.IdField(description="The id of this meeting.")
    committee_id = fields.RequiredForeignKeyField(
        description="The id of the committee of this meeting.",
        to=Collection("committee"),
        related_name="meeting_ids",
    )
    name = fields.RequiredCharField(description="The name of this meeting.")
