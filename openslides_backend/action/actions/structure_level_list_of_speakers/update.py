from datetime import datetime
from typing import Any

from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ....models.models import StructureLevelListOfSpeakers
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("structure_level_list_of_speakers.update")
class StructureLevelListOfSpeakersUpdateAction(UpdateAction):
    model = StructureLevelListOfSpeakers()
    schema = DefaultSchema(StructureLevelListOfSpeakers()).get_update_schema(
        optional_properties=["initial_time", "current_start_time", "remaining_time"],
        additional_optional_fields={
            "spoken_time": {"type": "integer", "minimum": 0},
        },
    )
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    def validate_instance(self, instance: dict[str, Any]) -> None:
        super().validate_instance(instance)
        if not self.internal:
            for field in ("current_start_time", "spoken_time"):
                if field in instance:
                    raise ActionException(field + " is not allowed to be set.")

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        if "initial_time" in instance:
            for field in ("current_start_time", "spoken_time", "remaining_time"):
                if field in instance:
                    raise ActionException(
                        f"Cannot set initial_time and {field} at the same time."
                    )
            instance["remaining_time"] = instance["initial_time"]
        elif "remaining_time" in instance and "spoken_time" in instance:
            raise ActionException(
                "Cannot set remaining_time and spoken_time at the same time."
            )

        if (t := instance.get("current_start_time")) and isinstance(t, int):
            instance["current_start_time"] = datetime.fromtimestamp(t)

        if spoken_time := instance.pop("spoken_time", None):
            db_instance = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                ["remaining_time"],
            )
            instance["remaining_time"] = db_instance["remaining_time"] - spoken_time
        return instance
