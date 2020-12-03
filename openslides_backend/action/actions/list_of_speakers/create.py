from ....models.models import ListOfSpeakers
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.default_schema import DefaultSchema


# This action is not registered because you can not call it from outside.
class ListOfSpeakersCreate(CreateActionWithInferredMeeting):
    name = "list_of_speakers.create"
    model = ListOfSpeakers()
    schema = DefaultSchema(ListOfSpeakers()).get_create_schema(["content_object_id"])

    relation_field_for_meeting = "content_object_id"
