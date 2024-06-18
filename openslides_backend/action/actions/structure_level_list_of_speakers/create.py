from typing import Any

from openslides_backend.action.mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.filters import And, FilterOperator
from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ....models.models import StructureLevelListOfSpeakers
from ....permissions.permissions import Permissions
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("structure_level_list_of_speakers.create")
class StructureLevelListOfSpeakersCreateAction(CreateActionWithInferredMeeting):
    model = StructureLevelListOfSpeakers()
    schema = DefaultSchema(StructureLevelListOfSpeakers()).get_create_schema(
        required_properties=["structure_level_id", "list_of_speakers_id"],
        optional_properties=["initial_time"],
    )
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    relation_field_for_meeting = "list_of_speakers_id"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)

        filter = And(
            FilterOperator("structure_level_id", "=", instance["structure_level_id"]),
            FilterOperator("list_of_speakers_id", "=", instance["list_of_speakers_id"]),
            FilterOperator("meeting_id", "=", instance["meeting_id"]),
        )
        if self.datastore.exists(collection=self.model.collection, filter=filter):
            raise ActionException(
                "(structure_level_id, list_of_speakers_id) must be unique."
            )

        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            ["list_of_speakers_default_structure_level_time"],
        )
        default_time = meeting.get("list_of_speakers_default_structure_level_time")
        if not default_time:
            raise ActionException("Structure level countdowns are deactivated")
        if "initial_time" not in instance:
            instance["initial_time"] = default_time
        instance["remaining_time"] = instance["initial_time"]
        return instance
