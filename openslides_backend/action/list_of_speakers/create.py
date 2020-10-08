from typing import Any, Dict

from ...models.models import ListOfSpeakers
from ...shared.exceptions import ActionException
from ...shared.patterns import Collection, FullQualifiedId
from ..default_schema import DefaultSchema
from ..generics import CreateAction


# This action is not registered because you can not call it from outside.
class ListOfSpeakersCreate(CreateAction):
    name = "list_of_speakers.create"
    model = ListOfSpeakers()
    schema = DefaultSchema(ListOfSpeakers()).get_create_schema(["content_object_id"])

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjusts content object and meeting.
        """
        # Parse content_object_id.
        collection_name, id = instance["content_object_id"].split("/")
        instance["content_object_id"] = FullQualifiedId(
            Collection(collection_name), int(id)
        )
        # Fetch meeting_id
        content_object = self.fetch_model(instance["content_object_id"], ["meeting_id"])
        if not content_object.get("meeting_id"):
            raise ActionException("Given content object has no meeting id.")
        instance["meeting_id"] = content_object["meeting_id"]
        return instance
