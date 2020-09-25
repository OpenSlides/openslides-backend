from ..shared.patterns import Collection
from . import fields
from .base import Model


class Assignment(Model):
    """
    Model for assignment.

    Reverse fields:
        candidate_ids: (assignment_candidate/assignment_id)[];
        poll_ids: (assignment_poll/assignment_id)[];
    """

    collection = Collection("assignment")
    verbose_name = "assignment"

    id = fields.IdField(description="The id of this assignment.")
    meeting_id = fields.RequiredForeignKeyField(
        description="The id of the meeting of this assignment.",
        to=Collection("meeting"),
        related_name="assignment_ids",
    )
    title = fields.RequiredCharField(description="The title of this assignment.")
    description = fields.TextField(description="The description of this assignment.")
    open_posts = fields.PositiveIntegerField(
        description="The open posts of this assignment."
    )
    phase = fields.PositiveIntegerField(
        description="The phase of this assignment.", enum=[1, 2, 3]
    )
    default_poll_description = fields.CharField(
        description="The default_poll_description of this assignment."
    )
    number_poll_candidates = fields.BooleanField(
        description="If assignment poll candidates are numbered."
    )
    agenda_item_id = fields.OneToOneField(
        description="The id of the agenda item of this assignment.",
        to=Collection("agenda_item"),
        related_name="content_object_id",
        generic_relation=True,
        delete_protection=True,
    )
    list_of_speakers_id = fields.ForeignKeyField(
        description="The id of list_of_speakers of this assignment.",
        to=Collection("list_of_speakers"),
        related_name="content_object_id",
        generic_relation=True,
        delete_protection=True,
    )
    attachment_ids = fields.ManyToManyArrayField(
        description="The attachments that should be related with this assignment.",
        to=Collection("mediafile"),
        related_name="attachment_ids",
        generic_relation=True,
    )
    tag_ids = fields.ManyToManyArrayField(
        description="The tags that should be related with this assignment.",
        to=Collection("tag"),
        related_name="tagged_ids",
        generic_relation=True,
    )

    # TODO:
    # projection_ids: (projection/element_id)[];  // use generic ManyToManyArrayField
    # current_projector_ids: (projector/current_element_ids)[];  // use generic ManyToManyArrayField
