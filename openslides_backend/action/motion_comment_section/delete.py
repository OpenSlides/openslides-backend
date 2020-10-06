from ...models.models import MotionCommentSection
from ..default_schema import DefaultSchema
from ..generics import DeleteAction
from ..register import register_action


@register_action("motion_comment_section.delete")
class MotionCommentSectionDeleteAction(DeleteAction):
    """
    Delete Action with check for empty comments.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_delete_schema()
