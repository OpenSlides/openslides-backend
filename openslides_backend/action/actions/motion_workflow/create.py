from typing import Any, Dict, List, Type

from ....models.models import MotionWorkflow
from ....shared.interfaces.event import EventType
from ....shared.patterns import FullQualifiedId
from ...action import Action
from ...generics.create import CreateAction
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
        return [
            {
                "name": MOTION_STATE_DEFAULT_NAME,
                "workflow_id": instance["id"],
                "first_state_of_workflow_id": instance["id"],
            }
        ]


@register_action("motion_workflow.create_simple_workflow")
class MotionWorkflowCreateSimpleWorkflowAction(CreateAction):
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates one instance of the payload. This can be overridden by custom
        action classes. Meant to be called inside base_update_instance.
        """
        additional_relation_models: Dict[FullQualifiedId, Any] = {
            FullQualifiedId(self.model.collection, instance["id"]): instance
        }
        payload = [
            {
                "name": "submitted",
                "allow_create_poll": True,
                "allow_support": True,
                "workflow_id": instance["id"],
                "first_state_of_workflow_id": instance["id"],
            },
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
        ]

        write_requests, action_results = self.execute_other_action(
            MotionStateActionSet.get_action("create"),
            payload,
            additional_relation_models,
        )
        additional_relation_models.update(
            {
                event["fqid"]: event["fields"]
                for event in write_requests.events  # type: ignore
                if event["type"] == EventType.Create
            }
        )
        first_state_id = action_results[0]["id"]  # type: ignore
        next_state_ids = [ar["id"] for ar in action_results[-3:]]  # type: ignore
        payload = [{"id": first_state_id, "next_state_ids": next_state_ids}]
        self.execute_other_action(
            MotionStateActionSet.get_action("update"),
            payload,
            additional_relation_models,
        )
        return instance
