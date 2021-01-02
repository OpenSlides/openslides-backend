from ....models.models import MotionCommentSection
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_comment_section.update")
class MotionCommentSectionUpdateAction(UpdateAction):
    """
    Action to update motion comment sections.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_update_schema(
        optional_properties=["name", "read_group_ids", "write_group_ids"]
    )
    permission_description = "motion.can_manage"
