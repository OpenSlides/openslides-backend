from typing import Any, Dict

from ...models.fields import Field
from ...shared.exceptions import ActionException, DatastoreException
from ...shared.patterns import Collection, FullQualifiedField, FullQualifiedId
from .calculated_field_handler import CalculatedFieldHandler
from .typing import ListUpdateElement, RelationUpdates


class MeetingUserIdsHandler(CalculatedFieldHandler):
    """
    CalculatedFieldsHandler to fill the field meeting.user_ids. It is a union of
    meeting.temporary_user_ids, meeting.guest_ids and all users in all groups of the
    meeting. This handles all necessary field updates simultaniously.
    """

    def process_field(
        self, field: Field, field_name: str, instance: Dict[str, Any], action: str
    ) -> RelationUpdates:
        # Try to fetch db instance to compare if any new ids were added
        fqid = FullQualifiedId(field.own_collection, instance["id"])
        try:
            db_instance = self.datastore.get(fqid, [field_name, "meeting_id"])
        except DatastoreException:
            db_instance = {}
        db_ids_set = set(db_instance.get(field_name, []) or [])
        ids_set = set(instance.get(field_name, []) or [])
        added_ids = ids_set.difference(db_ids_set)
        removed_ids = db_ids_set.difference(ids_set)

        if not added_ids and not removed_ids:
            return {}

        if field.own_collection == Collection("meeting"):
            meeting_id = instance["id"]
        elif field.own_collection == Collection("group"):
            meeting_id = instance.get("meeting_id")
            if not meeting_id:
                meeting_id = db_instance["meeting_id"]
                if not meeting_id:
                    raise ActionException(
                        f"No meeting_id found for group/{instance['id']}"
                    )

        relation_el: ListUpdateElement = {
            "type": "list_update",
            "add": list(added_ids),
            "remove": list(removed_ids),
        }
        fqfield = FullQualifiedField(Collection("meeting"), meeting_id, "user_ids")
        return {fqfield: relation_el}
