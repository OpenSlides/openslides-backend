from typing import Any, Dict

from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.util.action_type import ActionType
from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ....models.models import StructureLevelListOfSpeakers
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("structure_level_list_of_speakers.update", ActionType.BACKEND_INTERNAL)
class StructureLevelListOfSpeakersUpdateAction(UpdateAction):
    model = StructureLevelListOfSpeakers()
    schema = DefaultSchema(StructureLevelListOfSpeakers()).get_update_schema(
        optional_properties=["current_start_time"],
        additional_optional_fields={
            "spoken_time": {"type": "integer", "minimum": 1},
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        db_instance = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["remaining_time"],
        )
        if spoken_time := instance.pop("spoken_time", None):
            instance["remaining_time"] = db_instance["remaining_time"] - spoken_time
        return instance
