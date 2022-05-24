from typing import Any, Dict

from ...models.fields import Field
from ...shared.patterns import to_fqfield, to_fqid
from .calculated_field_handler import CalculatedFieldHandler
from .typing import ListUpdateElement, RelationUpdates


class UserMeetingIdsHandler(CalculatedFieldHandler):
    """
    CalculatedFieldHandler to fill the user.meeting_ids.
    """

    def process_field(
        self, field: Field, field_name: str, instance: Dict[str, Any], action: str
    ) -> RelationUpdates:
        if field_name != "group_$_ids":
            return {}

        fqid = to_fqid(field.own_collection, instance["id"])
        db_instance = self.datastore.get(
            fqid,
            [field_name],
            use_changed_models=False,
            raise_exception=False,
        )
        db_ids_set = set(db_instance.get(field_name, []) or [])
        ids_set = set(instance.get(field_name, []) or [])
        added_ids = ids_set.difference(db_ids_set)
        removed_ids = db_ids_set.difference(ids_set)

        if not added_ids and not removed_ids:
            return {}

        relation_el: ListUpdateElement = {
            "type": "list_update",
            "add": [int(x) for x in added_ids],
            "remove": [int(x) for x in removed_ids],
        }
        fqfield = to_fqfield("user", instance["id"], "meeting_ids")
        return {fqfield: relation_el}
