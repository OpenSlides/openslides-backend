from ...models.models import Tag
from ..action import register_action_set
from ..action_set import ActionSet
from ..default_schema import DefaultSchema


@register_action_set("tag")
class TagActionSet(ActionSet):
    """
    Actions to create, update and delete tags.
    """

    model = Tag()
    create_schema = DefaultSchema(Tag()).get_create_schema(
        properties=["name", "meeting_id"], required_properties=["name", "meeting_id"],
    )
    update_schema = DefaultSchema(Tag()).get_update_schema(properties=["name"])
    delete_schema = DefaultSchema(Tag()).get_delete_schema()
