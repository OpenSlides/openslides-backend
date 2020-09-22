from ..shared.patterns import Collection
from . import fields
from .base import Model


class MotionState(Model):
    """
    Model for motion state.

    There are the following reverse relation fields:
        motion_ids: (motion/state_id)[];
        motion_recommendation_ids: (motion/recommendation_id)[];
        first_state_of_workflow_id: motion_workflow/first_state_id;
        previous_state_ids: (motion_state/next_state_ids)[];
    """

    collection = Collection("motion_state")
    verbose_name = "motion state"

    id = fields.IdField(description="The id of this motion state.")
    name = fields.RequiredCharField(description="The name of this motion state.")
    recommendation_label = fields.CharField(
        description="The recommendation label of this motion state."
    )
    css_class = fields.CharField(
        description="The css class of this motion state.",
        enum=["gray", "red", "green", "lightblue", "yellow"],
    )
    restrictions = fields.ArrayField(
        description="The restrictions of this motion state.",
        items={
            "type": "string",
            "enum": [
                "motions.can_see_internal",
                "motions.can_manage_metadata",
                "motions.can_manage",
                "is_submitter",
            ],
        },
    )
    allow_support = fields.BooleanField(
        description="If this motion state allows supporting motions."
    )
    allow_create_poll = fields.BooleanField(
        description="If this motion state allows creating polls."
    )
    allow_submitter_edit = fields.BooleanField(
        description="If this motion state allows submitter to edit the motion."
    )
    set_number = fields.BooleanField(
        description="If this motion state sets number of motion when activated."
    )
    show_state_extension_field = fields.BooleanField(
        description="If in this motion state the state extension field is visable."
    )
    merge_amendment_into_final = fields.IntegerField(
        description="Unknown description.", enum=[-1, 0, 1]
    )
    show_recommendation_extension_field = fields.BooleanField(
        description="If in this motion state the recommendation extension field is visable."
    )

    workflow_id = fields.RequiredForeignKeyField(
        description="The id of the workflow of this motion state.",
        to=Collection("motion_workflow"),
        related_name="state_ids",
    )

    next_state_ids = fields.ManyToManyArrayField(
        description="The ids of the states that follow this state.",
        to=Collection("motion_state"),
        related_name="previous_state_ids",
    )
