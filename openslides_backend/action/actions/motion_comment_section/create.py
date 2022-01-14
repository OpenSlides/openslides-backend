from typing import Any, Dict

from ....models.models import MotionCommentSection
from ....permissions.permissions import Permissions
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_comment_section.create")
class MotionCommentSectionCreateAction(SequentialNumbersMixin):
    """
    Create Action with default weight.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_create_schema(
        required_properties=["name", "meeting_id"],
        optional_properties=["read_group_ids", "write_group_ids"],
    )
    permission = Permissions.Motion.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        instance["sequential_number"] = self.get_sequential_number(
            instance["meeting_id"]
        )
        return instance
