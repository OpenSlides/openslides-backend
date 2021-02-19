from typing import Any, Dict, List, Type

from ....models.models import MotionWorkflow
from ....shared.interfaces.event import EventType
from ...action import Action
from ...mixins.create_action_with_dependencies import CreateActionWithDependencies
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..motion_state.create_update_delete import MotionStateActionSet

MOTION_STATE_DEFAULT_NAME = "default"


@register_action("motion_workflow.create")
class MotionWorkflowCreateAction(CreateActionWithDependencies):
    """
    Action to create a motion workflow.
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_create_schema(["name", "meeting_id"])
    dependencies = [MotionStateActionSet.get_action("create")]

    def get_dependent_action_payload(
        self, instance: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> List[Dict[str, Any]]:
        return [{
            "name": MOTION_STATE_DEFAULT_NAME,
            "workflow_id": instance["id"],
            "first_state_of_workflow_id": instance["id"],
        }]


@register_action("motion_workflow.create_simple_workflow")
class MotionWorkflowCreateSimpleWorkflowAction(CreateActionWithDependencies):
    """
    Action to create a motion workflow.
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_create_schema(
        ["name", "meeting_id"],
        [
            "default_workflow_meeting_id",
            "default_amendment_workflow_meeting_id",
            "default_statute_amendment_workflow_meeting_id",
            "first_state_id",
        ],
    )
    dependencies = [MotionStateActionSet.get_action("create")]

    def get_dependent_action_payload(
        self, instance: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> List[Dict[str, Any]]:
        """
        Umbau in 2 execute_other: 1. ANlegen aller 4, 2. update der first mit den next steps
        """
        next_state_ids: List[int] = []
        #if index == 3:
        for wr in self.write_requests:
            for event in wr.events:  # type: ignore
                if (
                    event["fqid"].collection.collection == "motion_state"
                    and event["type"] == EventType.Create
                    and event["fields"]["workflow_id"] == instance["id"]
                ):
                    next_state_ids.append(event["fields"]["id"])
                    self.additional_relation_models[event["fqid"]] = event["fields"]
        return [
            {
                "name": "accepted",
                "recommendation_label": "Acceptance",
                "css_class": "green",
                "merge_amendment_into_final": "do_merge",
                "workflow_id": instance["id"],
            },
            {
                "name": "rejected",
                "recommendation_label": "Rejection",
                "css_class": "red",
                "merge_amendment_into_final": "do_not_merge",
                "workflow_id": instance["id"],
            },
            {
                "name": "not_decided",
                "recommendation_label": "No decision",
                "css_class": "grey",
                "merge_amendment_into_final": "do_not_merge",
                "workflow_id": instance["id"],
            },
            {
                "name": "submitted",
                "allow_create_poll": True,
                "allow_support": True,
                "workflow_id": instance["id"],
                "first_state_of_workflow_id": instance["id"],
                "next_state_ids": next_state_ids,
            },
        ]
