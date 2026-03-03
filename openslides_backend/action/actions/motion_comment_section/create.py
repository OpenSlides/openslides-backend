from typing import Any

from ....models.models import MotionCommentSection
from ....permissions.permissions import Permissions
from ...mixins.forbid_anonymous_group_mixin import ForbidAnonymousGroupMixin
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_comment_section.create")
class MotionCommentSectionCreateAction(
    SequentialNumbersMixin, ForbidAnonymousGroupMixin
):
    """
    Create Action with default weight.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_create_schema(
        required_properties=["name", "meeting_id"],
        optional_properties=[
            "read_group_ids",
            "write_group_ids",
            "submitter_can_write",
        ],
    )
    permission = Permissions.Motion.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        self.check_anonymous_not_in_list_fields(instance, ["write_group_ids"])
        return super().update_instance(instance)
