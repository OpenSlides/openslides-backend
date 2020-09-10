from ..shared.patterns import Collection
from . import fields
from .base import Model


class MotionWorkflow(Model):
    """
    Model for motion workflow.

    There are the following reverse relation fields:
        state_ids: (motion_state/workflow_id)[];
        default_workflow_meeting_id: meeting/motions_default_workflow_id;
        default_amendment_workflow_meeting_id: meeting/motions_default_amendment_workflow_id;
        default_statute_amendment_workflow_meeting_id: meeting/motions_default_statute_amendment_workflow_id;
    """

    collection = Collection("motion_workflow")
    verbose_name = "motion workflow"

    id = fields.IdField(description="The id of this motion workflow.")
    name = fields.RequiredCharField(
        description="The name of this motion workflow.", maxLength=255
    )

    meeting_id = fields.RequiredForeignKeyField(
        description="The id of the meeting of this motion workflow.",
        to=Collection("meeting"),
        related_name="motion_workflow_ids",
    )
    first_state_id = fields.RequiredOneToOneField(
        description="The id of the first state of this motion workflow.",
        to=Collection("motion_state"),
        related_name="first_state_of_workflow_id",
    )
