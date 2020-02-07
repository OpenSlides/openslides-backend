from ..shared.patterns import Collection
from . import fields
from .base import Model


class Motion(Model):
    """
    Model for motions.
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
    identifier = fields.CharField(
        description="The customizable human readable identifier of this motion."
    )
    serial_number = fields.PositiveIntegerField(
        description="The (positive) serial number of this motion. This number is auto-generated and read-only."
    )

    # Content
    title = fields.RequiredCharField(
        description="The title or headline of this motion."
    )
    text = fields.TextField(description="The HTML formatted main text of this motion.")
    modified_final_version = fields.TextField(
        description="the HTML formatted modified final version ot motion's main text."
    )
    # amendment_paragraph_ # TODO
    reason = fields.TextField(
        description="The HTML formatted reason text of this motion."
    )
    motion_statute_paragraph_id = fields.ForeignKeyField(
        description="The statute paragraph this motions refers to.",
        to=Collection("motion_statute_paragraph"),
        related_name="motion_ids",
    )

    # Sort and structure, category, block, origin
    sort_parent_id = fields.ForeignKeyField(
        description="Parent field for multi-depth sorting of motions.",
        to=Collection("motion"),
        related_name="sort_children_ids",
    )
    sort_weight = fields.IntegerField(
        description="Weight field for sorting of motions."
    )
    parent_id = fields.ForeignKeyField(
        description="Parent field for structuring of motions as amendments.",
        to=Collection("motion"),
        related_name="amendment_ids",
    )
    motion_category_id = fields.ForeignKeyField(
        description="The category of this motion.",
        to=Collection("motion_category"),
        related_name="motion_ids",
    )
    category_weight = fields.IntegerField(
        description="Used for sorting of motions inside the category."
    )
    motion_block_id = fields.ForeignKeyField(
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
    # (TODO: Do we really need workflow_id.)
    state_id = fields.RequiredForeignKeyField(
        description="The state of this motion.",
        to=Collection("motion_state"),
        related_name="motion_active_ids",
    )
    state_extension = fields.CharField(
        description="The description of some special states."
    )
    recommendation_id = fields.ForeignKeyField(
        description="The recommended state of this motion.",
        to=Collection("motion_state"),
        related_name="motion_recommended_ids",
    )
    recommendation_extension = fields.CharField(
        description="The description of some special recommended states."
    )

    # User
    supporter_ids = fields.ManyToManyArrayField(
        description="The users that are supportes of this motion.",
        to=Collection("user"),
        related_name="motion_supported_ids",
    )

    # Timestamps
    created = fields.TimestampField(
        description="Unix timestamp when this motion was created."
    )
    last_modified = fields.TimestampField(
        description="Unix timestamp when this motion was modifed last."
    )

    # Miscellaneous
    mediafile_attachment_ids = fields.ManyToManyArrayField(
        description="The attachments that should be referenced with this motion.",
        to=Collection("mediafile_attachment"),
        related_name="motion_ids",
    )
    tag_ids = fields.ManyToManyArrayField(
        description="The tags that should be referenced with this motion.",
        to=Collection("tag"),
        related_name="motion_ids",
    )

    # Nur Rückreferenzen, deshalb keine Felddefinitionen.
    # submitter_ids
    # poll_ids
    # change_recommendation_ids
    # comment_ids
    # agenda_item_id: agenda_item;
    # list_of_speakers_id: list_of_speakers;
