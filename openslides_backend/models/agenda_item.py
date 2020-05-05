from ..shared.patterns import Collection
from . import fields
from .base import Model


class AgendaItem(Model):
    """
    Model for agenda items.

    There are the following reverse relation fields:
        content_object_id: */agenda_item_id;
        child_ids: (agenda_item/parent_id)[];
    """

    collection = Collection("agenda_item")
    verbose_name = "agenda item"

    id = fields.IdField(description="The id of this agenda item.")
    meeting_id = fields.RequiredForeignKeyField(
        description="The id of the meeting of this agenda item.",
        to=Collection("meeting"),
        related_name="agenda_item_ids",
    )
    item_number = fields.CharField(
        description="The number or human readable identifier of this agenda item."
    )
    comment = fields.TextField(description="A comment on this agenda item.")

    # closed = fields.BooleanField()
    # type = number;
    # is_internal: boolean;
    # is_hidden: boolean;
    # duration: number; // in seconds
    # weight: number;
    # level: number; // calculated.
    # parent_id: agenda_item/child_ids;
    # current_projector_ids: (projector/current_element_ids)[]
    # projection_ids: (projection/element_id)[];
