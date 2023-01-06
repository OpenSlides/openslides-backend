from typing import Any, Dict

from ...models.fields import Field
from ...shared.patterns import (
    fqfield_from_collection_and_id_and_field,
    fqid_from_collection_and_id,
)
from .calculated_field_handler import CalculatedFieldHandler
from .typing import ListUpdateElement, RelationUpdates


class UserMeetingIdsHandler(CalculatedFieldHandler):
    """
    CalculatedFieldHandler to fill the user.meeting_ids.
    """

    def process_field(
        self, field: Field, field_name: str, instance: Dict[str, Any], action: str
    ) -> RelationUpdates:
        if field_name != "group_ids":
            return {}

        fqid = fqid_from_collection_and_id(field.own_collection, instance["id"])
        db_instance = self.datastore.get(
            fqid,
            [field_name, "user_id", "meeting_id"],
            use_changed_models=False,
            raise_exception=False,
        )
        meeting_id = (
            instance["meeting_id"]
            if instance.get("meeting_id")
            else db_instance["meeting_id"]
        )
        user_id = (
            instance["user_id"] if instance.get("user_id") else db_instance["user_id"]
        )
        added_ids = (
            [meeting_id]
            if not db_instance.get("group_ids") and instance.get("group_ids")
            else []
        )
        removed_ids = (
            [meeting_id]
            if db_instance.get("group_ids") and not instance.get("group_ids")
            else []
        )

        if not added_ids and not removed_ids:
            return {}

        relation_el: ListUpdateElement = {
            "type": "list_update",
            "add": added_ids,
            "remove": removed_ids,
        }
        fqfield = fqfield_from_collection_and_id_and_field(
            "user", user_id, "meeting_ids"
        )
        return {fqfield: relation_el}
