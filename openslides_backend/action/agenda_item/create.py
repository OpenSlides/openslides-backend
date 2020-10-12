from ...models.models import AgendaItem
from ..create_action_with_inferred_meeting import CreateActionWithInferredMeeting
from ..default_schema import DefaultSchema
from ..register import register_action


@register_action("agenda_item.create")
class AgendaItemCreate(CreateActionWithInferredMeeting):
    """
    Action to create agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_create_schema(
        required_properties=["content_object_id"],
        optional_properties=[
            "item_number",
            "comment",
            "type",
            "parent_id",
            "duration",
            "weight",
        ],
    )

    relation_field_for_meeting = "content_object_id"
