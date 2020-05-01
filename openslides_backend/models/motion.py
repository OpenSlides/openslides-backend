from ..shared.patterns import Collection
from . import fields
from .base import Model


class Motion(Model):
    """
    Model for motions.

    There are the following reverse relation fields:
        amendment_ids: (motion/lead_motion_id)[]
        sort_child_ids: (motion/sort_parent_id)[]
        derived_motion_ids: (motion/origin_id)[]  // Note: The related motions may not be in the same meeting
        submitter_ids: (motion_submitter/motion_id)[]
        poll_ids: (motion_poll/motion_id)[]
        change_recommendation_ids: (motion_change_recommendation/motion_id)[]
        comment_ids: (motion_comment/motion_id)[]
    """

    collection = Collection("motion")
    verbose_name = "motion"

    # Identifers
    id = fields.IdField(description="The id of this motion.")
    meeting_id = fields.RequiredForeignKeyField(
        description="The id of the meeting of this motion.",
        to=Collection("meeting"),
        related_name="motion_ids",
    )
    number = fields.CharField(
        description="The customizable human readable number or identifier of this motion."
    )
    sequential_number = fields.PositiveIntegerField(
        description="The (positive) serial number of this motion. This number is auto-generated and read-only."
    )

    # Content
    title = fields.RequiredCharField(
        description="The title or headline of this motion."
    )
    text = fields.TextField(description="The HTML formatted main text of this motion.")
    modified_final_version = fields.TextField(
        description="The HTML formatted modified final version ot motion's main text."
    )
    # TODO: amendment_paragraph_$<paragraph_number>: HTML;
    reason = fields.TextField(
        description="The HTML formatted reason text of this motion."
    )
    statute_paragraph_id = fields.ForeignKeyField(
        description="The statute paragraph this motions refers to.",
        to=Collection("motion_statute_paragraph"),
        related_name="motion_ids",
    )

    # Sort and structure, category, block, origin
    sort_parent_id = fields.ForeignKeyField(
        description="Parent field for multi-depth sorting of motions.",
        to=Collection("motion"),
        related_name="sort_child_ids",
    )
    sort_weight = fields.IntegerField(
        description="Weight field for sorting of motions."
    )
    lead_motion_id = fields.ForeignKeyField(
        description="Parent field for structuring of motions as amendments.",
        to=Collection("motion"),
        related_name="amendment_ids",
    )
    category_id = fields.ForeignKeyField(
        description="The category of this motion.",
        to=Collection("motion_category"),
        related_name="motion_ids",
    )
    category_weight = fields.IntegerField(
        description="Used for sorting of motions inside the category."
    )
    block_id = fields.ForeignKeyField(
        description="The block of this motion.",
        to=Collection("motion_block"),
        related_name="motion_ids",
    )
    origin_id = fields.ForeignKeyField(
        description="The original motion in another meeting.",
        to=Collection("motion"),
        related_name="derived_motion_ids",
    )

    # State and recommendation
    state_id = fields.RequiredForeignKeyField(
        description="The state of this motion.",
        to=Collection("motion_state"),
        related_name="motion_ids",
    )
    state_extension = fields.CharField(
        description="The description of some special states."
    )
    recommendation_id = fields.ForeignKeyField(
        description="The recommended state of this motion.",
        to=Collection("motion_state"),
        related_name="motion_recommendation_ids",
    )
    recommendation_extension = fields.CharField(
        description="The description of some special recommended states."
    )

    # User
    supporter_ids = fields.ManyToManyArrayField(
        description="The users that are supportes of this motion.",
        to=Collection("user"),
        related_name="supported_motion_$_ids",
        structured_relation="meeting_id",
    )

    # Timestamps
    created = fields.TimestampField(
        description="Unix timestamp when this motion was created."
    )
    last_modified = fields.TimestampField(
        description="Unix timestamp when this motion was modifed last."
    )

    # Miscellaneous
    attachment_ids = fields.ManyToManyArrayField(
        description="The attachments that should be related with this motion.",
        to=Collection("mediafile"),
        related_name="attachment_ids",
        generic_relation=True,
    )
    tag_ids = fields.ManyToManyArrayField(
        description="The tags that should be related with this motion.",
        to=Collection("tag"),
        related_name="tagged_ids",
        generic_relation=True,
    )
    # TODO:
    # projection_ids: (projection/element_id)[];  // use generic ManyToManyArrayField
    # current_projector_ids: (projector/current_element_ids)[];  // use generic ManyToManyArrayField
    # personal_note_ids: (personal_note/content_object_id)[];  // use generic ManyToManyArrayField
    # agenda_item_id: agenda_item/content_object_id;  // use generic ForeignKeyField
    # list_of_speakers_id: list_of_speakers/content_object_id;  // use generic ForeignKeyField
