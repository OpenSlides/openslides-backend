from typing import Any, cast

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
        self, field: Field, field_name: str, instance: dict[str, Any], action: str
    ) -> RelationUpdates:
        if field_name != "group_ids":
            return {}
        fqid = fqid_from_collection_and_id(field.own_collection, instance["id"])
        assert (changed_model := self.datastore.get_changed_model(fqid))
        assert changed_model.get(field_name) == instance.get(field_name)
        db_instance = self.datastore.get(
            fqid,
            [field_name, "user_id", "meeting_id"],
            use_changed_models=False,
            raise_exception=False,
        )
        if not (meeting_id := instance.get("meeting_id")):
            if not (
                meeting_id := cast(
                    dict[str, Any], self.datastore.get_changed_model(fqid)
                ).get("meeting_id")
            ):
                meeting_id = db_instance.get("meeting_id")
        assert meeting_id, f"No meeting_id can be found for fqid {fqid}"

        if not (user_id := instance.get("user_id")):
            if not (
                user_id := cast(
                    dict[str, Any], self.datastore.get_changed_model(fqid)
                ).get("user_id")
            ):
                user_id = db_instance.get("user_id")
        assert user_id, f"No user_id can be found for fqid {fqid}"

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
