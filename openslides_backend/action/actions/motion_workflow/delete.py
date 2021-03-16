from typing import Any, Dict, List, cast

from ....models.models import MotionWorkflow
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        check if is default or last workflow of meeting.
        """
        workflow = self.datastore.fetch_model(
            FullQualifiedId(Collection("motion_workflow"), instance["id"]),
            ["meeting_id"],
        )
        meeting = self.datastore.fetch_model(
            FullQualifiedId(Collection("meeting"), int(workflow["meeting_id"])),
            [
                "motions_default_workflow_id",
                "motions_default_amendment_workflow_id",
                "motions_default_statute_amendment_workflow_id",
                "motion_workflow_ids",
            ],
        )
        if instance["id"] in (
            meeting.get("motions_default_workflow_id"),
            meeting.get("motions_default_amendment_workflow_id"),
            meeting.get("motions_default_statute_amendment_workflow_id"),
        ):
            raise ActionException("Cannot delete a default workflow.")

        workflow_ids = cast(List[int], meeting.get("motion_workflow_ids"))
        if len(workflow_ids) == 1:
            raise ActionException("Cannot delete the last workflow of a meeting.")

        return instance
