from openslides_backend.action.generics.create import CreateAction

from ....models.models import StructureLevel
from ....permissions.permissions import Permissions
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("structure_level.create")
class StructureLevelCreateAction(CreateAction):
    model = StructureLevel()
    schema = DefaultSchema(StructureLevel()).get_create_schema(
        required_properties=["meeting_id", "name"],
        optional_properties=["color", "default_time"],
    )
    permission = Permissions.User.CAN_MANAGE
