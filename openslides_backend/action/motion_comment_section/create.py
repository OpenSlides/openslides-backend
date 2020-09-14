from typing import Any, Dict

from ...models.motion_comment_section import MotionCommentSection
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import CreateAction


@register_action("motion_comment_section.create")
class MotionCommentSectionCreateAction(CreateAction):
    """
    Create Action with default weight.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_create_schema(
        properties=["name", "meeting_id", "read_group_ids", "write_group_ids"],
        required_properties=["name", "meeting_id"],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        set default weight to instance.
        """
        instance["weight"] = instance.get("weight", 0)
        return instance
