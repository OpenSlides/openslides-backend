from typing import Any, Dict

from ...models.models import AgendaItem
from ...shared.patterns import Collection, FullQualifiedId
from ..base import ActionPayload
from ..create_action_with_inferred_meeting import CreateActionWithInferredMeeting
from ..default_schema import DefaultSchema
from ..register import register_action


@register_action("agenda_item.create")
class AgendaItemCreate(CreateActionWithInferredMeeting):
    """
    Action to create agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_create_schema(
        required_properties=["content_object_id"],
        optional_properties=[
            "item_number",
            "comment",
            "type",
            "parent_id",
            "duration",
            "weight",
        ],
    )

    relation_field_for_meeting = "content_object_id"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        If parent_id is given, set weight to parent.weight + 1
        """
        instance = super().update_instance(instance)
        if instance.get("parent_id") is None:
            return instance
        parent = self.database.get(
            FullQualifiedId(Collection("agenda_item"), instance["parent_id"]),
            ["weight"],
        )
        if parent.get("weight") is None:
            return instance
        instance["weight"] = parent["weight"] + 1
        return instance

    def get_updated_instances(self, payload: ActionPayload) -> ActionPayload:
        for instance in payload:
            if instance.get("parent_id") is None:
                parent = {"is_hidden": False, "is_internal": False}
                instance["level"] = 0
            else:
                parent = self.database.get(
                    FullQualifiedId(self.model.collection, instance["parent_id"]),
                    ["is_hidden", "is_internal", "level"],
                )
                instance["level"] = parent.get("level", 0) + 1
            instance["is_hidden"] = instance.get(
                "type"
            ) == AgendaItem.HIDDEN_ITEM or parent.get("is_hidden", False)
            instance["is_internal"] = instance.get(
                "type"
            ) == AgendaItem.INTERNAL_ITEM or parent.get("is_internal", False)

        return payload
