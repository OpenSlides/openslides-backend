from typing import Any, Dict

from ...models.fields import Field
from ...shared.patterns import (
    fqfield_from_collection_and_id_and_field,
    fqid_from_collection_and_id,
)
from .calculated_field_handler import CalculatedFieldHandler
from .typing import ListUpdateElement, RelationUpdates


class MeetingUserIdsHandler(CalculatedFieldHandler):
    """
    CalculatedFieldsHandler to fill the field meeting.user_ids.
    It uses all users in all groups of the meeting.
    This handles all necessary field updates simultaniously.
    """

    def process_field(
        self, field: Field, field_name: str, instance: Dict[str, Any], action: str
    ) -> RelationUpdates:
        # Try to fetch db instance to compare if any new ids were added
        fqid = fqid_from_collection_and_id(field.own_collection, instance["id"])
        db_instance = self.datastore.get(
            fqid,
            [field_name, "meeting_id"],
            use_changed_models=False,
            raise_exception=False,
        )
        db_ids_set = set(db_instance.get(field_name, []) or [])
        ids_set = set(instance.get(field_name, []) or [])
        added_ids = ids_set.difference(db_ids_set)
        removed_ids = db_ids_set.difference(ids_set)

        meeting_id = instance.get("meeting_id") or db_instance.get("meeting_id")
        if not meeting_id:
            new_instance = self.datastore.get(fqid, ["meeting_id"])
            meeting_id = new_instance.get("meeting_id")
        assert isinstance(meeting_id, int)

        # check if removed_ids should actually be removed
        # cast to list to be able to alter it while iterating
        for id in list(removed_ids):
            user_fqid = fqid_from_collection_and_id("user", id)
            if not self.datastore.is_deleted(user_fqid):
                group_field = f"group_${meeting_id}_ids"
                user = self.datastore.get(user_fqid, [group_field])
                if user.get(group_field):
                    removed_ids.remove(id)

        if not added_ids and not removed_ids:
            return {}

        relation_el: ListUpdateElement = {
            "type": "list_update",
            "add": list(added_ids),
            "remove": list(removed_ids),
        }
        fqfield = fqfield_from_collection_and_id_and_field(
            "meeting", meeting_id, "user_ids"
        )
        return {fqfield: relation_el}
