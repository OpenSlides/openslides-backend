from ....models.models import Group
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("group.update")
class GroupUpdateAction(UpdateAction):
    """
    Action to update a group.
    """

    model = Group()
    schema = DefaultSchema(Group()).get_update_schema(optional_properties=["name"])
    permission_description = "user.can_manage"
