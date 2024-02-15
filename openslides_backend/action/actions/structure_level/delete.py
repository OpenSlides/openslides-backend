from ....models.models import StructureLevel
from ....permissions.permissions import Permissions
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("structure_level.delete")
class StructureLevelDeleteAction(DeleteAction):
    model = StructureLevel()
    schema = DefaultSchema(StructureLevel()).get_delete_schema()
    permission = Permissions.User.CAN_MANAGE
