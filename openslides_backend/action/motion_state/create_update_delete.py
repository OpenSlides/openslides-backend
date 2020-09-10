from ...models.motion_state import MotionState
from ..action import register_action_set
from ..action_set import ActionSet
from ..default_schema import DefaultSchema


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
