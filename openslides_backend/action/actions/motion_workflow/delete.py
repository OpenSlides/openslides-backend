from typing import Any

from ....models.models import MotionWorkflow
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_workflow.delete")
class MotionWorkflowDeleteAction(DeleteAction):
    """
    Action to delete a motion workflow
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_delete_schema()
    permission = Permissions.Motion.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        check if is default or last workflow of meeting.
        """
        workflow = self.datastore.get(
            fqid_from_collection_and_id("motion_workflow", instance["id"]),
            ["meeting_id"],
        )
        if not self.is_meeting_to_be_deleted(workflow["meeting_id"]):
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", workflow["meeting_id"]),
                [
                    "motions_default_workflow_id",
                    "motions_default_amendment_workflow_id",
                    "motion_workflow_ids",
                ],
            )
            if instance["id"] == meeting.get("motions_default_workflow_id"):
                raise ActionException(
                    "You cannot delete the workflow as long as it is selected as default workflow for new motions in the settings. Please set another workflow as default in the settings and try to delete the workflow again."
                )
            if instance["id"] == meeting.get("motions_default_amendment_workflow_id"):
                raise ActionException(
                    "You cannot delete the workflow as long as it is selected as default workflow for new amendments in the settings. Please set another workflow as default in the settings and try to delete the workflow again."
                )

        return instance
