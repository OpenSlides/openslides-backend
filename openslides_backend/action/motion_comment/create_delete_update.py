from ...models.motion_comment import MotionComment
from ..action import register_action_set
from ..action_set import ActionSet
from ..default_schema import DefaultSchema


@register_action_set("motion_comment")
class MotionCommentActionSet(ActionSet):
    """
    Actions to create, update and delete motion comment.
    """

    model = MotionComment()
    create_schema = DefaultSchema(MotionComment()).get_create_schema(
        properties=["comment", "motion_id", "section_id"],
        required_properties=["comment", "motion_id", "section_id"],
    )
    update_schema = DefaultSchema(MotionComment()).get_update_schema(
        properties=["comment"]
    )
    delete_schema = DefaultSchema(MotionComment()).get_delete_schema()
