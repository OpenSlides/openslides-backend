from typing import Any, Dict

from ...models.models import MotionState
from ..action import register_action_set
from ..action_set import ActionSet
from ..default_schema import DefaultSchema
from ..generics import CreateAction, DeleteAction, UpdateAction


class MotionStateCreateAction(CreateAction):
    """
    Create action to set defaults.
    """

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set default for restrictions.
        """
        instance["restrictions"] = instance.get("restrictions", [])
        instance["merge_amendment_into_final"] = instance.get(
            "merge_amendment_into_final", 0
        )
        return instance


@register_action_set("motion_state")
class MotionStateActionSet(ActionSet):
    """
    Actions to create, update and delete motion states.
    """

    model = MotionState()
    create_schema = DefaultSchema(MotionState()).get_create_schema(
        properties=[
            "name",
            "workflow_id",
            "recommendation_label",
            "css_class",
            "restrictions",
            "allow_support",
            "allow_create_poll",
            "allow_submitter_edit",
            "set_number",
            "show_state_extension_field",
            "merge_amendment_into_final",
            "show_recommendation_extension_field",
        ],
        required_properties=["name", "workflow_id"],
    )
    update_schema = DefaultSchema(MotionState()).get_update_schema(
        properties=[
            "name",
            "recommendation_label",
            "css_class",
            "restrictions",
            "allow_support",
            "allow_create_poll",
            "allow_submitter_edit",
            "set_number",
            "show_state_extension_field",
            "merge_amendment_into_final",
            "show_recommendation_extension_field",
            "next_state_ids",
            "previous_state_ids",
        ]
    )
    delete_schema = DefaultSchema(MotionState()).get_delete_schema()
    routes = {
        "create": MotionStateCreateAction,
        "update": UpdateAction,
        "delete": DeleteAction,
    }
