from typing import Any

from ....models.models import ListOfSpeakers
from ....shared.patterns import fqid_from_collection_and_id
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ...util.default_schema import DefaultSchema


# This action is not registered because you can not call it from outside.
class ListOfSpeakersCreate(SequentialNumbersMixin, CreateActionWithInferredMeeting):
    name = "list_of_speakers.create"
    model = ListOfSpeakers()
    schema = DefaultSchema(ListOfSpeakers()).get_create_schema(["content_object_id"])

    relation_field_for_meeting = "content_object_id"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            ["list_of_speakers_initially_closed"],
            lock_result=False,
        )
        instance["closed"] = meeting.get("list_of_speakers_initially_closed", False)
        return instance
