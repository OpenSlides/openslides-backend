from typing import Any, Dict

from openslides_backend.services.datastore.interface import InstanceAdditionalBehaviour

from ...models.fields import Field
from ...shared.patterns import Collection, FullQualifiedField, FullQualifiedId
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

        fqid = FullQualifiedId(field.own_collection, instance["id"])
        db_instance = self.datastore.get(
            fqid,
            [field_name],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
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
        fqfield = FullQualifiedField(Collection("user"), instance["id"], "meeting_ids")
        return {fqfield: relation_el}
