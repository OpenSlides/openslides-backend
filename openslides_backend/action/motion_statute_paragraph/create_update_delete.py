from typing import Any, Dict

from ...models.models import MotionStatuteParagraph
from ..action_set import ActionSet
from ..default_schema import DefaultSchema
from ..generics import CreateAction, DeleteAction, UpdateAction
from ..register import register_action_set


class MotionStatuteParagraphCreateAction(CreateAction):
    """
    Create action to set weight default in update_instance.
    """

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        set default for weight.
        """
        instance["weight"] = instance.get("weight", 0)
        return instance


@register_action_set("motion_statute_paragraph")
class MotionStatuteParagraphActionSet(ActionSet):
    """
    Actions to create, update and delete motion statute paragraph.
    """

    model = MotionStatuteParagraph()
    create_schema = DefaultSchema(MotionStatuteParagraph()).get_create_schema(
        required_properties=["meeting_id", "title"], optional_properties=["text"],
    )
    update_schema = DefaultSchema(MotionStatuteParagraph()).get_update_schema(
        optional_properties=["title"]
    )
    delete_schema = DefaultSchema(MotionStatuteParagraph()).get_delete_schema()
    routes = {
        "create": MotionStatuteParagraphCreateAction,
        "update": UpdateAction,
        "delete": DeleteAction,
    }
