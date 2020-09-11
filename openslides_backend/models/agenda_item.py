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

    AGENDA_ITEM = 1
    INTERNAL_ITEM = 2
    HIDDEN_ITEM = 3

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
    type = fields.IntegerField(
        description=f"The type of the agenda item (common, internal, hidden). Defaults to {AGENDA_ITEM}",
        enum=[AGENDA_ITEM, INTERNAL_ITEM, HIDDEN_ITEM],
    )
    parent_id = fields.ForeignKeyField(
        description="The id of the parent of this agenda item in agenda tree.",
        to=Collection("agenda_item"),
        related_name="child_ids",
    )
    duration = fields.PositiveIntegerField(
        description="The duration of this agenda item object in seconds."
    )
    weight = fields.IntegerField(
        description="The weight of the agenda item. Submitting null defaults to 0."
    )
    closed = fields.BooleanField(description="If this agenda item is closed.")
    tag_ids = fields.ManyToManyArrayField(
        description="The tags that should be related with this agenda item.",
        to=Collection("tag"),
        related_name="tagged_ids",
        generic_relation=True,
    )

    # TODO:
    # is_internal: boolean;  // calculated
    # is_hidden: boolean;  // calculated
    # level: number; // calculated.

    # TODO:
    # current_projector_ids: (projector/current_element_ids)[]
    # projection_ids: (projection/element_id)[];
