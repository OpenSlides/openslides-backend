from typing import Any, Dict

from openslides_backend.services.datastore.deleted_models_behaviour import (
    DeletedModelsBehaviour,
    InstanceAdditionalBehaviour,
)

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
        ids_set = set([int(x) for x in instance.get(field_name, []) or []])
        fqid = FullQualifiedId(field.own_collection, instance["id"])
        db_instance = self.datastore.fetch_model(
            fqid,
            [field_name],
            get_deleted_models=DeletedModelsBehaviour.NO_DELETED,
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
            exception=False,
        )
        db_ids_set = set([int(x) for x in db_instance.get(field_name, []) or []])
        added_ids = ids_set.difference(db_ids_set)
        removed_ids = db_ids_set.difference(ids_set)

        if not added_ids and not removed_ids:
            return {}
        relation_el: ListUpdateElement = {
            "type": "list_update",
            "add": list(added_ids),
            "remove": list(removed_ids),
        }
        fqfield = FullQualifiedField(Collection("user"), instance["id"], "meeting_ids")
        return {fqfield: relation_el}
