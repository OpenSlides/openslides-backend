from typing import Any

from openslides_backend.action.mixins.meeting_user_helper import get_meeting_user

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
        self, field: Field, field_name: str, instance: dict[str, Any], action: str
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
        mu_added_ids = ids_set.difference(db_ids_set)
        mu_removed_ids = db_ids_set.difference(ids_set)
        added_ids = self.get_user_ids(mu_added_ids)
        removed_ids = self.get_user_ids(mu_removed_ids)

        meeting_id = instance.get("meeting_id") or db_instance.get("meeting_id")
        if not meeting_id:
            new_instance = self.datastore.get(fqid, ["meeting_id"])
            meeting_id = new_instance.get("meeting_id")
        assert isinstance(meeting_id, int)

        # check if removed_ids should actually be removed
        # cast to list to be able to alter it while iterating
        for id_ in list(removed_ids):
            user_fqid = fqid_from_collection_and_id("user", id_)
            if not self.datastore.is_deleted(user_fqid):
                meeting_user = get_meeting_user(
                    self.datastore, meeting_id, id_, ["id", "group_ids"]
                )
                if meeting_user and meeting_user.get("group_ids"):
                    removed_ids.remove(id_)

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

    def get_user_ids(self, meeting_user_ids: set[int]) -> list[int]:
        user_ids: list[int] = []
        for id_ in meeting_user_ids:
            fqid = fqid_from_collection_and_id("meeting_user", id_)
            meeting_user = self.datastore.get(
                fqid,
                ["user_id"],
                use_changed_models=not self.datastore.is_deleted(fqid),
            )
            user_ids.append(meeting_user["user_id"])
        return user_ids
