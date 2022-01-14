from typing import Any, Dict

from ....models.models import MotionStatuteParagraph
from ....permissions.permissions import Permissions
from ...action_set import ActionSet
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action_set


class MotionStatuteParagraphCreate(SequentialNumbersMixin):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        instance["sequential_number"] = self.get_sequential_number(
            instance["meeting_id"]
        )
        return instance


@register_action_set("motion_statute_paragraph")
class MotionStatuteParagraphActionSet(ActionSet):
    """
    Actions to create, update and delete motion statute paragraph.
    """

    model = MotionStatuteParagraph()
    create_schema = DefaultSchema(MotionStatuteParagraph()).get_create_schema(
        required_properties=["meeting_id", "title", "text"],
        optional_properties=[],
    )
    update_schema = DefaultSchema(MotionStatuteParagraph()).get_update_schema(
        optional_properties=["title", "text"]
    )
    delete_schema = DefaultSchema(MotionStatuteParagraph()).get_delete_schema()
    permission = Permissions.Motion.CAN_MANAGE

    CreateActionClass = MotionStatuteParagraphCreate
