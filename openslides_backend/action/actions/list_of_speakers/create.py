from typing import Any, Dict

from ....models.models import ListOfSpeakers
from ....shared.patterns import to_fqid
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        meeting = self.datastore.get(
            to_fqid("meeting", instance["meeting_id"]),
            ["list_of_speakers_initially_closed"],
        )
        instance["closed"] = meeting.get("list_of_speakers_initially_closed", False)
        return instance
