from ....models.models import Role
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .deduplicate_permissions_mixin import DeduplicatePermissionsMixin


@register_action("role.update")
class RoleUpdateAction(DeduplicatePermissionsMixin, UpdateAction):
    """
    Action to update a role.
    """

    model = Role()
    schema = DefaultSchema(Role()).get_update_schema(
        optional_properties=["name", "permissions"]
    )
