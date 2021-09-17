from typing import Any, Dict, List, Tuple, Type

from ....models.models import MotionWorkflow
from ....permissions.permissions import Permissions
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
    permission = Permissions.Motion.CAN_MANAGE
    dependencies = [MotionStateActionSet.get_action("create")]

    def get_dependent_action_data(
        self, instance: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> List[Dict[str, Any]]:
        return [
            {
                "name": MOTION_STATE_DEFAULT_NAME,
                "workflow_id": instance["id"],
                "first_state_of_workflow_id": instance["id"],
            }
        ]


@register_action("motion_workflow.create_simple_workflow", internal=True)
class MotionWorkflowCreateSimpleWorkflowAction(CreateAction):
    """
    Action to create a simple motion workflow.
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_create_schema(
        ["name", "meeting_id"],
        [
            "default_workflow_meeting_id",
            "default_amendment_workflow_meeting_id",
            "default_statute_amendment_workflow_meeting_id",
        ],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        self.apply_instance(instance)
        action_data = [
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

        action_results = self.execute_other_action(
            MotionStateActionSet.get_action("create"),
            action_data,
        )
        first_state_id = action_results[0]["id"]  # type: ignore
        next_state_ids = [ar["id"] for ar in action_results[-3:]]  # type: ignore
        action_data = [{"id": first_state_id, "next_state_ids": next_state_ids}]
        self.execute_other_action(
            MotionStateActionSet.get_action("update"),
            action_data,
        )
        return instance


@register_action("motion_workflow.create_complex_workflow", internal=True)
class MotionWorkflowCreateComplexWorkflowAction(CreateAction):
    """
    Action to create a complex motion workflow.
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_create_schema(
        ["name", "meeting_id"],
        [
            "default_workflow_meeting_id",
            "default_amendment_workflow_meeting_id",
            "default_statute_amendment_workflow_meeting_id",
        ],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        self.apply_instance(instance)
        action_data = [
            {
                "name": "in_progress",
                "allow_submitter_edit": True,
                # "dont_set_identifier": True,
                "workflow_id": instance["id"],
                "first_state_of_workflow_id": instance["id"],
            },
            {
                "name": "submitted",
                "allow_support": True,
                "workflow_id": instance["id"],
                # "dont_set_identifier": True,
            },
            {
                "name": "permitted",
                "allow_create_poll": True,
                "workflow_id": instance["id"],
                "recommendation_label": "Permission",
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
                "name": "withdrawed",
                "css_class": "grey",
                "merge_amendment_into_final": "do_not_merge",
                "workflow_id": instance["id"],
            },
            {
                "name": "adjourned",
                "recommendation_label": "Adjournment",
                "css_class": "grey",
                "merge_amendment_into_final": "do_not_merge",
                "workflow_id": instance["id"],
            },
            {
                "name": "not concerned",
                "recommendation_label": "No concernment",
                "css_class": "grey",
                "merge_amendment_into_final": "do_not_merge",
                "workflow_id": instance["id"],
            },
            {
                "name": "refered to committee",
                "recommendation_label": "Referral to committee",
                "css_class": "grey",
                "merge_amendment_into_final": "do_not_merge",
                "workflow_id": instance["id"],
            },
            {
                "name": "needs review",
                "css_class": "grey",
                "merge_amendment_into_final": "do_not_merge",
                "workflow_id": instance["id"],
            },
            {
                "name": "rejected (not authorized)",
                "recommendation_label": "Rejection (not authorized)",
                "css_class": "grey",
                "merge_amendment_into_final": "do_not_merge",
                "workflow_id": instance["id"],
            },
        ]

        action_results = self.execute_other_action(
            MotionStateActionSet.get_action("create"),
            action_data,
        )
        from_to: Tuple[Tuple[int, Tuple[int]]] = (  # type: ignore
            (0, (1, 5)),
            (1, (2, 5, 10)),
            (2, (3, 4, 5, 6, 7, 8, 9)),
        )
        action_data = [
            {
                "id": action_results[id]["id"],  # type: ignore
                "next_state_ids": [action_results[id]["id"] for id in next_state_ids],  # type: ignore
            }
            for id, next_state_ids in from_to
        ]
        self.execute_other_action(
            MotionStateActionSet.get_action("update"),
            action_data,
        )
        return instance
