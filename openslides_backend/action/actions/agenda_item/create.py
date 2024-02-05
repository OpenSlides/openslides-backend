from typing import Any

from ....models.models import AgendaItem
from ....permissions.permissions import Permissions
from ....shared.filters import And, FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


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
            "tag_ids",
        ],
    )
    permission = Permissions.AgendaItem.CAN_MANAGE

    relation_field_for_meeting = "content_object_id"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        If parent_id is given, set weight to parent.weight + 1
        """
        instance = super().update_instance(instance)

        if instance.get("parent_id") is None:
            parent = {"is_hidden": False, "is_internal": False, "level": -1}
        else:
            parent = self.datastore.get(
                fqid_from_collection_and_id(
                    self.model.collection, instance["parent_id"]
                ),
                ["is_hidden", "is_internal", "level"],
            )
        instance["level"] = parent.get("level", 0) + 1
        instance["is_hidden"] = instance.get(
            "type"
        ) == AgendaItem.HIDDEN_ITEM or parent.get("is_hidden", False)
        instance["is_internal"] = instance.get(
            "type"
        ) == AgendaItem.INTERNAL_ITEM or parent.get("is_internal", False)

        if "weight" not in instance:
            max_weight = self.datastore.max(
                self.model.collection,
                And(
                    FilterOperator("parent_id", "=", instance.get("parent_id")),
                    FilterOperator("meeting_id", "=", instance["meeting_id"]),
                ),
                "weight",
            )
            instance["weight"] = (max_weight or 0) + 1
        return instance
