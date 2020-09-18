from ...models.motion_comment_section import MotionCommentSection
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import DeleteAction


@register_action("motion_comment_section.delete")
class MotionCommentSectionDeleteAction(DeleteAction):
    """
    Delete Action with check for empty comments.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_delete_schema()
