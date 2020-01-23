from ..shared.patterns import Collection
from . import fields
from .base import Model


class Meeting(Model):
    """
    Model for meetings.
    """

    collection = Collection("meeting")
    verbose_name = "meeting"

    # TODO: Make to and related_name in relation fields optional.

    id = fields.IdField(description="An integer. The id of the meeting.")
    committee_id = fields.ForeignKeyField(
        description="An integer. The id of the committee of the meeting.",
        to="committee",
        related_name="meeting_ids",
    )
    title = fields.RequiredCharField(
        description="A string. The title or headline of the meeting."
    )
