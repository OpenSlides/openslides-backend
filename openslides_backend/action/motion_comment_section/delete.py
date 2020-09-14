from typing import Any, Dict

from ...models.motion_comment_section import MotionCommentSection
from ...shared.exceptions import ActionException
from ...shared.patterns import Collection, FullQualifiedId
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        check if comment_ids is empty.
        """
        id_ = int(str(instance.get("id")))
        model = self.database.get(
            FullQualifiedId(Collection("motion_comment_section"), id_)
        )
        if model.get("comment_ids"):
            raise ActionException(
                f"Cannot delete motion comment section '{id_}' with existing comments."
            )
        return instance
