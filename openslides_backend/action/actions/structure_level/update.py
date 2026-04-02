from openslides_backend.action.generics.update import UpdateAction

from ....models.models import StructureLevel
from ....permissions.permissions import Permissions
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("structure_level.update")
class StructureLevelUpdateAction(UpdateAction):
    model = StructureLevel()
    schema = DefaultSchema(StructureLevel()).get_update_schema(
        optional_properties=["name", "color", "default_time"],
    )
    permission = Permissions.User.CAN_MANAGE
