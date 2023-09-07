from typing import Any, Dict, List, Set, cast

from openslides_backend.services.datastore.commands import GetManyRequest

from ...models.fields import Field
from ...shared.filters import And, FilterOperator, Not
from ...shared.patterns import (
    FullQualifiedId,
    collection_from_fqid,
    fqfield_from_collection_and_id_and_field,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from ...shared.typing import DeletedModel
from .calculated_field_handler import CalculatedFieldHandler
from .typing import ListUpdateElement, RelationUpdates


class UserCommitteeCalculateHandler(CalculatedFieldHandler):
    """
    CalculatedFieldHandler to fill the user.committee_ids and the related committee.user_ids
    by catching modifications of MeetingUser.group_ids and User.committee_management_ids.
    A user belongs to a committee, if he is member of a meeting in the committee via group or
    he has rights on CommitteeManagementLevel.
    Problem: The changes come from 2 different collections, both could add or remove user/committee_relations.
    This method will calculate additions and removals by comparing the instances of datastore.changed_models and
    the stored db-content.
    Calculates per user on
    1. user.committee_managment_ids, if changed
    2. MeetingUser.group_ids of all changes
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
        assert (
            changed_model := self.datastore.changed_models.get(
                fqid_from_collection_and_id(field.own_collection, instance["id"])
            )
        )
        assert changed_model.get(field_name) == instance.get(field_name)
        if field.own_collection == "user":
            fqid_user = fqid_from_collection_and_id(
                field.own_collection, instance["id"]
            )
            user_id = instance["id"]
            db_user = self.datastore.get(
                fqid_user,
                ["id", "committee_ids", "committee_management_ids", "meeting_user_ids"],
                use_changed_models=False,
                raise_exception=False,
            )
            meeting_users = self.get_meeting_users_from_changed_models(user_id)
            return self.do_changes(fqid_user, db_user, meeting_users, action)
        else:
            if action != "user.delete":
                self.fill_meeting_user_changed_models_with_user_and_meeting_id()
            fqid_meeting_user = fqid_from_collection_and_id(
                field.own_collection, instance["id"]
            )
            user_id = cast(
                Dict[str, Any], self.datastore.changed_models.get(fqid_meeting_user)
            ).get("user_id")
            meeting_users = self.get_meeting_users_from_changed_models(user_id)
            fqid_user = fqid_from_collection_and_id("user", user_id)
            db_user = self.datastore.get(
                fqid_user,
                [
                    "id",
                    "committee_ids",
                    "committee_management_ids",
                    "meeting_user_ids",
                ],
                use_changed_models=False,
                raise_exception=False,
            )
            return self.do_changes(fqid_user, db_user, meeting_users, action)

    def do_changes(
        self,
        fqid: FullQualifiedId,
        db_user: Dict[str, Any],
        meeting_users: Dict[int, Dict[str, Any]],
        action: str,
    ) -> RelationUpdates:
        user_id = id_from_fqid(fqid)
        db_committee_ids = set(db_user.get("committee_ids", []) or [])
        changed_user = self.datastore.changed_models[fqid]
        if "committee_management_ids" in changed_user:
            new_committees_ids = set(changed_user["committee_management_ids"] or [])
        else:
            new_committees_ids = set(db_user.get("committee_management_ids", []))

        meeting_ids = self.get_all_meeting_ids_by_user_id(user_id, meeting_users)
        if meeting_ids:
            meeting_collection = "meeting"
            committee_ids: Set[int] = set(
                map(
                    lambda x: x.get("committee_id", 0),
                    self.datastore.get_many(
                        [
                            GetManyRequest(
                                meeting_collection,
                                meeting_ids,
                                ["committee_id"],
                            )
                        ]
                    )
                    .get(meeting_collection, {})
                    .values(),
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

    def fill_meeting_user_changed_models_with_user_and_meeting_id(self) -> None:
        meeting_user_ids: List[int] = [
            id_from_fqid(key)
            for key, data in self.datastore.changed_models.items()
            if collection_from_fqid(key) == "meeting_user"
            and (not data.get("user_id") or not data.get("meeting_id"))
        ]
        if meeting_user_ids:
            results = self.datastore.get_many(
                [
                    GetManyRequest(
                        "meeting_user",
                        meeting_user_ids,
                        ["user_id", "meeting_id"],
                    )
                ],
                use_changed_models=False,
            ).get("meeting_user", {})
            for key, value in results.items():
                changed_model = self.datastore.changed_models[
                    fqid_from_collection_and_id("meeting_user", key)
                ]
                changed_model["user_id"] = value["user_id"]
                changed_model["meeting_id"] = value["meeting_id"]

    def get_all_meeting_ids_by_user_id(
        self, user_id: int, meeting_users: Dict[int, Dict[str, Any]]
    ) -> List[int]:
        filter_ = And(
            FilterOperator("user_id", "=", user_id),
            Not(FilterOperator("group_ids", "=", None)),
        )
        res = self.datastore.filter(
            "meeting_user",
            filter_,
            ["meeting_id", "group_ids"],
        )
        meeting_ids = []
        for meeting_user_id, meeting_user in res.items():
            if meeting_user_id not in meeting_users and meeting_user["group_ids"]:
                meeting_ids.append(meeting_user["meeting_id"])
        meeting_ids.extend(
            [mu["meeting_id"] for mu in meeting_users.values() if mu.get("group_ids")]
        )
        return meeting_ids

    def get_meeting_users_from_changed_models(
        self, user_id: int
    ) -> Dict[int, Dict[str, Any]]:
        return {
            id_from_fqid(key): data
            for key, data in self.datastore.changed_models.items()
            if collection_from_fqid(key) == "meeting_user"
            and (data.get("user_id") == user_id or isinstance(data, DeletedModel))
        }
