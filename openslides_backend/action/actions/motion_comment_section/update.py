from typing import Any

from ....models.models import MotionCommentSection
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...mixins.forbid_anonymous_group_mixin import ForbidAnonymousGroupMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_comment_section.update")
class MotionCommentSectionUpdateAction(UpdateAction, ForbidAnonymousGroupMixin):
    """
    Action to update motion comment sections.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_update_schema(
        optional_properties=[
            "name",
            "read_group_ids",
            "write_group_ids",
            "submitter_can_write",
        ]
    )
    permission = Permissions.Motion.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        self.check_anonymous_not_in_list_fields(instance, ["write_group_ids"])
        return super().update_instance(instance)
