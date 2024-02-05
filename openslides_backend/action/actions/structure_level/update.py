from typing import Any

from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.mixins.check_unique_name_mixin import (
    CheckUniqueInContextMixin,
)

from ....models.models import StructureLevel
from ....permissions.permissions import Permissions
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("structure_level.update")
class StructureLevelUpdateAction(CheckUniqueInContextMixin, UpdateAction):
    model = StructureLevel()
    schema = DefaultSchema(StructureLevel()).get_update_schema(
        optional_properties=["name", "color", "default_time"],
    )
    permission = Permissions.User.CAN_MANAGE

    def validate_instance(self, instance: dict[str, Any]) -> None:
        super().validate_instance(instance)
        self.check_unique_in_context(
            "name",
            instance["name"],
            "The name of the structure level must be unique.",
            instance["id"],
            "meeting_id",
            self.get_meeting_id(instance),
        )
