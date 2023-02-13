from typing import Any, Dict, List, Set, cast

from openslides_backend.services.datastore.commands import GetManyRequest

from ...models.fields import Field
from ...shared.filters import FilterOperator
from ...shared.patterns import (
    fqfield_from_collection_and_id_and_field,
    fqid_from_collection_and_id,
)
from .calculated_field_handler import CalculatedFieldHandler
from .typing import ListUpdateElement, RelationUpdates


class UserCommitteeCalculateHandler(CalculatedFieldHandler):
    """
    CalculatedFieldHandler to fill the user.committee_ids and the related committee.user_ids
    by catching modifications of UserMeeting.group_ids and User.committee_management_ids.
    A user belongs to a committee, if he is member of a meeting in the committee via group or
    he has rights on CommitteeManagementLevel.
    """

    def process_field(
        self, field: Field, field_name: str, instance: Dict[str, Any], action: str
    ) -> RelationUpdates:
        if (
            (field.own_collection != "user" and field.own_collection != "meeting_user")
            or field_name not in ["group_ids", "committee_management_ids"]
            or ("group_ids" in instance and field_name != "group_ids")
        ):
            return {}
        user_id = instance["id"]
        fqid = fqid_from_collection_and_id(field.own_collection, instance["id"])
        db_user = self.datastore.get(
            fqid,
            ["committee_ids", "committee_management_ids"],
            use_changed_models=False,
            raise_exception=False,
        )
        db_committee_ids = set(db_user.get("committee_ids", []) or [])
        if "committee_management_ids" in instance:
            new_committees_ids = set(instance["committee_management_ids"])
        else:
            new_committees_ids = set(db_user.get("committee_management_ids", []))
        if "group_ids" in instance:
            meeting_ids = self.get_meetings(
                user_id, instance["id"], instance["group_ids"]
            )
        else:
            meeting_ids = self.get_meetings(user_id, -1, [])
        meeting_collection = "meeting"
        committee_ids: Set[int] = set(
            map(
                lambda x: x.get("committee_id", 0),
                self.datastore.get_many(
                    [
                        GetManyRequest(
                            meeting_collection,
                            list(meeting_ids),
                            ["committee_id"],
                        )
                    ]
                )
                .get(meeting_collection, {})
                .values(),
            )
        )
        new_committees_ids.update(committee_ids)
        committee_ids = set(
            committee_id
            for meeting_id in meeting_ids
            if (
                committee_id := self.datastore.changed_models.get(
                    fqid_from_collection_and_id("meeting", meeting_id), {}
                ).get("committee_id")
            )
        )
        new_committees_ids.update(committee_ids)
        added_ids = new_committees_ids - db_committee_ids
        removed_ids = db_committee_ids - new_committees_ids

        if not added_ids and not removed_ids:
            return {}

        relation_update: RelationUpdates = {}
        if not action == "user.delete":
            fqfield_user = fqfield_from_collection_and_id_and_field(
                "user", user_id, "committee_ids"
            )
            relation_el: ListUpdateElement = {
                "type": "list_update",
                "add": [int(x) for x in added_ids],
                "remove": [int(x) for x in removed_ids],
            }
            relation_update[fqfield_user] = relation_el

        def add_relation(add: bool, set_: Set[int]) -> None:
            for committee_id in set_:
                fqfield_committee = fqfield_from_collection_and_id_and_field(
                    "committee", committee_id, "user_ids"
                )
                relation_update[fqfield_committee] = {
                    "type": "list_update",
                    "add": [user_id] if add else cast(List[int], []),
                    "remove": [] if add else [user_id],  # type: ignore
                }

        if not action == "committee.delete":
            add_relation(True, added_ids)
            add_relation(False, removed_ids)
        return relation_update

    def get_meeting_users_by_user_id(self, user_id: int) -> List[Dict[str, Any]]:
        """Get a user_id, filters all meeting_user for it, and returns the
        dicts with id, meeting_id and group_ids."""
        filter_ = FilterOperator("user_id", "=", user_id)
        res = self.datastore.filter(
            "meeting_user",
            filter_,
            ["id", "meeting_id", "group_ids"],
        )
        return list(res.values())

    def replace_changed_meeting_user(
        self, replace_id: int, group_ids: List[int], meeting_users: List[Dict[str, Any]]
    ) -> None:
        """Replace the meeting user which group ids has been changed."""
        for meeting_user in meeting_users:
            if meeting_user["id"] == replace_id:
                meeting_user["group_ids"] = group_ids

    def get_meetings(
        self, user_id: int, replace_id: int, group_ids: List[int]
    ) -> Set[int]:
        meeting_users = self.get_meeting_users_by_user_id(user_id)
        self.replace_changed_meeting_user(replace_id, group_ids, meeting_users)
        meeting_ids = [mu["meeting_id"] for mu in meeting_users if mu.get("group_ids")]
        return set(meeting_ids)
