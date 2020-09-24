from ...models.models import MotionCommentSection
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import UpdateAction


@register_action("motion_comment_section.update")
class MotionCommentSectionUpdateAction(UpdateAction):
    """
    Action to update motion comment sections.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_update_schema(
        properties=["name", "read_group_ids", "write_group_ids"]
    )
