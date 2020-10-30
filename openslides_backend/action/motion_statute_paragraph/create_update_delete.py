from ...models.models import MotionStatuteParagraph
from ..action_set import ActionSet
from ..default_schema import DefaultSchema
from ..register import register_action_set


@register_action_set("motion_statute_paragraph")
class MotionStatuteParagraphActionSet(ActionSet):
    """
    Actions to create, update and delete motion statute paragraph.
    """

    model = MotionStatuteParagraph()
    create_schema = DefaultSchema(MotionStatuteParagraph()).get_create_schema(
        required_properties=["meeting_id", "title", "text"], optional_properties=[],
    )
    update_schema = DefaultSchema(MotionStatuteParagraph()).get_update_schema(
        optional_properties=["title", "text"]
    )
    delete_schema = DefaultSchema(MotionStatuteParagraph()).get_delete_schema()
