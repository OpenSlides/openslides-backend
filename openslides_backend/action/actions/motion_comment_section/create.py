from ....models.models import MotionCommentSection
from ....permissions.permissions import Permissions
from ...generics.create import CreateAction
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_comment_section.create")
class MotionCommentSectionCreateAction(SequentialNumbersMixin, CreateAction):
    """
    Create Action with default weight.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_create_schema(
        required_properties=["name", "meeting_id"],
        optional_properties=["read_group_ids", "write_group_ids"],
    )
    permission = Permissions.Motion.CAN_MANAGE
