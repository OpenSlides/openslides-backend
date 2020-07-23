from ..shared.patterns import Collection
from . import fields
from .base import Model


class Group(Model):
    """
    Model for groups.

    There are the following reverse relation fields:
        TODO
    """

    # TODO: Add reverse relation fields to docstring.

    collection = Collection("group")
    verbose_name = "group"

    id = fields.IdField(description="The id of this group.")

    used_as_motion_poll_default_id = fields.ForeignKeyField(
        description="Point to the meeting if members of this group have voting rights for motion poll by default",
        to=Collection("meeting"),
        related_name="motion_poll_default_group_ids",
    )
    used_as_assignment_poll_default_id = fields.ForeignKeyField(
        to=Collection("meeting"), related_name="assignment_poll_default_group_ids"
    )

    # TODO: Add all fields.
