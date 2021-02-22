from typing import Any, Dict

from ....models.models import Projector
from ....shared.patterns import FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projector.control_view")
class ProjectorControlView(UpdateAction):
    """
    Action to control view a projector.
    """

    model = Projector()
    schema = DefaultSchema(Projector()).get_update_schema(
        additional_required_fields={
            "field": {"type": "string", "enum": ["scale", "scroll"]},
            "direction": {"type": "string", "enum": ["up", "down", "reset"]},
        },
        additional_optional_fields={
            "step": {"type": "integer"},
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        field = instance.pop("field")
        direction = instance.pop("direction")
        step = instance.pop("step", 1)

        if direction == "reset":
            new_value = 0
        elif direction == "up":
            projector = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), [field]
            )
            new_value = projector.get(field, 0) + step
        elif direction == "down":
            projector = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), [field]
            )
            new_value = projector.get(field, 0) - step
        instance[field] = new_value
        return instance
