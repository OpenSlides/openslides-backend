from typing import Any, Dict

from ...models.motion_workflow import MotionWorkflow
from ...shared.exceptions import ActionException
from ...shared.patterns import Collection, FullQualifiedId
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import CreateAction, DeleteAction, UpdateAction


@register_action("motion_workflow.create")
class MotionWorkflowCreateAction(CreateAction):
    """
    Action to create a motion workflow.
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_create_schema(
        properties=["name", "meeting_id"], required_properties=["name", "meeting_id"],
    )


@register_action("motion_workflow.update")
class MotionWorkflowUpdateAction(UpdateAction):
    """
    Action to update a motion workflow.
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_update_schema(
        properties=["name", "first_state_id"]
    )


@register_action("motion_workflow.delete")
class MotionWorkflowDeleteAction(DeleteAction):
    """
    Action to delete a motion workflow
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_delete_schema()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        check meeting.motions_default_workflow_id and
        meeting.motions_default_statute_amendment_workflow_id
        """
        workflow = self.fetch_model(
            FullQualifiedId(Collection("motion_workflow"), instance["id"]),
            ["meeting_id"],
        )
        meeting = self.fetch_model(
            FullQualifiedId(Collection("meeting"), int(workflow["meeting_id"])),
            [
                "motions_default_workflow_id",
                "motions_default_amendment_workflow_id",
                "motions_default_statute_amendment_workflow_id",
            ],
        )
        if instance["id"] == meeting.get("motions_default_workflow_id"):
            raise ActionException("Cannot delete a default workflow.")
        if instance["id"] == meeting.get("motions_default_amendment_workflow_id"):
            raise ActionException("Cannot delete a default workflow.")
        if instance["id"] == meeting.get(
            "motions_default_statute_amendment_workflow_id"
        ):
            raise ActionException("Cannot delete a default workflow.")
        return instance
