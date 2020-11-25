from ...models.models import Role
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action
from .deduplicate_permissions_mixin import DeduplicatePermissionsMixin


@register_action("role.create")
class RoleCreate(DeduplicatePermissionsMixin, CreateAction):
    """
    Action to create roles.
    """

    model = Role()
    schema = DefaultSchema(Role()).get_create_schema(
        required_properties=["organisation_id", "name"],
        optional_properties=["permissions"],
    )
