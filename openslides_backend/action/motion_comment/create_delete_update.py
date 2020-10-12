from ...models.models import MotionComment
from ..action_set import ActionSet
from ..create_action_with_inferred_meeting import (
    get_create_action_with_inferred_meeting,
)
from ..default_schema import DefaultSchema
from ..register import register_action_set


@register_action_set("motion_comment")
class MotionCommentActionSet(ActionSet):
    """
    Actions to create, update and delete motion comment.
    """

    model = MotionComment()
    create_schema = DefaultSchema(MotionComment()).get_create_schema(
        ["comment", "motion_id", "section_id"],
    )
    update_schema = DefaultSchema(MotionComment()).get_update_schema(
        optional_properties=["comment"]
    )
    delete_schema = DefaultSchema(MotionComment()).get_delete_schema()

    CreateActionClass = get_create_action_with_inferred_meeting("motion_id")
