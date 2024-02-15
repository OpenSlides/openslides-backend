from typing import Any

from openslides_backend.action.generics.create import CreateAction
from openslides_backend.action.mixins.check_unique_name_mixin import (
    CheckUniqueInContextMixin,
)

from ....models.models import StructureLevel
from ....permissions.permissions import Permissions
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("structure_level.create")
class StructureLevelCreateAction(CheckUniqueInContextMixin, CreateAction):
    model = StructureLevel()
    schema = DefaultSchema(StructureLevel()).get_create_schema(
        required_properties=["meeting_id", "name"],
        optional_properties=["color", "default_time"],
    )
    permission = Permissions.User.CAN_MANAGE

    def validate_instance(self, instance: dict[str, Any]) -> None:
        super().validate_instance(instance)
        self.check_unique_in_context(
            "name",
            instance["name"],
            "The name of the structure level must be unique.",
            context_id=instance["meeting_id"],
            context_name="meeting_id",
        )
