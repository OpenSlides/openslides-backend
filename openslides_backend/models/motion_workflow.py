from ..shared.patterns import Collection
from . import fields
from .base import Model


class MotionWorkflow(Model):
    """
    Model for motion workflow.

    Reverse fields:
    - state_ids
    """

    collection = Collection("motion_workflow")
    verbose_name = "motion_workflow"

    id = fields.IdField(description="The id of this motion workflow.")
    meeting_id = fields.RequiredForeignKeyField(
        description="The id of the meeting of this motion workflow.",
        to=Collection("meeting"),
        related_name="motion_workflow_ids",
    )
    name = fields.RequiredCharField(
        description="The name of this motion workflow.", maxLength=255
    )
    first_state_id = fields.RequiredForeignKeyField(
        description="The first_state_id of this motion workflow.",
        to=Collection("motion_state"),
        related_name="first_state_of_workflow_id",
    )
    default_workflow_meeting_id = fields.ForeignKeyField(
        description="The default_workflow_meeting_id of this motion workflow.",
        to=Collection("meeting"),
        related_name="motions_default_workflow_id",
    )
    default_statute_amendments_meeting_id = fields.ForeignKeyField(
        description="The default_statute_amendments_meeting_id of this motion workflow.",
        to=Collection("meeting"),
        related_name="motions_default_statute_amendments_workflow_id",
    )
