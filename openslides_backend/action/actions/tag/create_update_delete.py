from ....models.models import Tag
from ....permissions.permissions import Permissions
from ...action_set import ActionSet
from ...util.default_schema import DefaultSchema
from ...util.register import register_action_set


@register_action_set("tag")
class TagActionSet(ActionSet):
    """
    Actions to create, update and delete tags.
    """

    model = Tag()
    create_schema = DefaultSchema(Tag()).get_create_schema(["name", "meeting_id"])
    update_schema = DefaultSchema(Tag()).get_update_schema(optional_properties=["name"])
    delete_schema = DefaultSchema(Tag()).get_delete_schema()
    permission = Permissions.Tag.CAN_MANAGE
