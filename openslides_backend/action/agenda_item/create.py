from typing import Any, Dict

from ...models.models import AgendaItem
from ...shared.exceptions import ActionException
from ...shared.patterns import Collection, FullQualifiedId
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action


@register_action("agenda_item.create")
class AgendaItemCreate(CreateAction):
    """
    Action to create agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_create_schema(
        properties=[
            "item_number",
            "comment",
            "content_object_id",
            "type",
            "parent_id",
            "duration",
            "weight",
        ],
        required_properties=["content_object_id"],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjusts content object and meeting and sets defaults for type and weight
        """
        # Parse content_object_id.
        collection_name, id = instance["content_object_id"].split("/")
        instance["content_object_id"] = FullQualifiedId(
            Collection(collection_name), int(id)
        )
        instance["type"] = instance.get("type", AgendaItem.AGENDA_ITEM)
        instance["weight"] = instance.get("weight", 0)
        # Fetch meeting_id
        content_object = self.fetch_model(instance["content_object_id"], ["meeting_id"])
        if not content_object.get("meeting_id"):
            raise ActionException("Given content object has no meeting id.")
        instance["meeting_id"] = content_object["meeting_id"]
        # assert parent_id is valid
        if "parent_id" in instance:
            parent_item = self.fetch_model(
                FullQualifiedId(self.model.collection, instance["parent_id"]),
                ["meeting_id"],
            )
            if not parent_item.get("meeting_id") == instance["meeting_id"]:
                raise ActionException("Given parent_id is invalid.")
        return instance
