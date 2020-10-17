from ...models.models import MotionCommentSection
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action


@register_action("motion_comment_section.create")
class MotionCommentSectionCreateAction(CreateAction):
    """
    Create Action with default weight.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_create_schema(
        required_properties=["name", "meeting_id"],
        optional_properties=["read_group_ids", "write_group_ids"],
    )
