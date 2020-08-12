from ..shared.patterns import Collection
from . import fields
from .base import Model


class MotionState(Model):
    """
    Model for motion state.

    Reverse fields:
    - motion_ids
    - motion_recommendation_ids
    """

    collection = Collection("motion_state")
    verbose_name = "motion_state"

    id = fields.IdField(description="The id of this motion state.")
    name = fields.RequiredCharField(description="The name of this motion state.")
    recommendation_label = fields.CharField(
        description="The recommendation label of this motion state."
    )
    css_class = fields.CharField(description="The css class of this motion state.")
    restrictions = fields.ArrayField(
        description="The restrictions of this motion state."
    )
    allow_support = fields.BooleanField(
        description="If this motion state allow_support."
    )
    allow_create_poll = fields.BooleanField(
        description="If this motion state allow_create_poll."
    )
    allow_submitter_edit = fields.BooleanField(
        description="If this motion state allow_submitter_edit."
    )
    set_number = fields.BooleanField(description="If this motion state set_number.")
    show_state_extension_field = fields.BooleanField(
        description="If this motion state show_state_extension_field."
    )
    merge_amendment_into_final = fields.PositiveIntegerField(
        description="The merge_amendment_into_final of this motion state."
    )
    show_recommendation_extension_field = fields.BooleanField(
        description="If this motion state show_recommendation_extension_field."
    )

    workflow_id = fields.ForeignKeyField(
        description="The id of the workflow of this motion state.",
        to=Collection("motion_workflow"),
        related_name="state_ids",
    )
    first_state_of_workflow_id = fields.ForeignKeyField(
        description="The first_state_of_workflow_id of this motion state.",
        to=Collection("motion_workflow"),
        related_name="first_state_id",
    )

    # TODO next_state_ids: (motion_state/previous_state_ids)[];
    # TODO previous_state_ids: (motion_state/next_state_ids)[];
