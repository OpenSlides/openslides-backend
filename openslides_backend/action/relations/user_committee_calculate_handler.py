from typing import Any, Dict, List, Set, cast

from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.services.datastore.interface import InstanceAdditionalBehaviour

from ...models.fields import Field
from ...shared.patterns import Collection, FullQualifiedField, FullQualifiedId
from .calculated_field_handler import CalculatedFieldHandler
from .typing import ListUpdateElement, RelationUpdates


class UserCommitteeCalculateHandler(CalculatedFieldHandler):
    """
    CalculatedFieldHandler to fill the user.committee_ids and the opposite committee.user_ids.
    Catches fields user.committee_$_management_level and user.group_$_ids
    A user belongs to a committee, if he is member of a meeting in the committee via group or
    he has rights on CommitteeManagementLevel. Last one is user field only, i.e. with no
    back relation from committee. That's the reason that all relations between
    the two collections are only set via user, even committee.create/change make calls
    to user.change-actions.
    Backend Issue1071: Prevent changes for deleted committees
    """

    def process_field(
        self, field: Field, field_name: str, instance: Dict[str, Any], action: str
    ) -> RelationUpdates:
        if field_name not in ["group_$_ids", "committee_$_management_level"] or (
            "group_$_ids" in instance and field_name != "group_$_ids"
        ):
            return {}
        user_id: int = instance["id"]
        fqid = FullQualifiedId(Collection("user"), user_id)
        db_user = self.datastore.fetch_model(
            fqid,
            ["committee_ids", "group_$_ids", "committee_$_management_level"],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
            exception=False,
        )
        db_committee_ids = set(db_user.get("committee_ids", []) or [])
        db_committee_cml = set(
            map(int, db_user.get("committee_$_management_level", []) or [])
        )
        detected_deleted_committee_ids = db_committee_cml - db_committee_ids
        if "committee_$_management_level" in instance:
            new_committees_ids = set(
                map(int, instance.get("committee_$_management_level", [])) or []
            )
        else:
            new_committees_ids = set(
                map(int, db_user.get("committee_$_management_level", [])) or []
            )
        if "group_$_ids" in instance:
            meeting_ids = list(map(int, instance.get("group_$_ids", []))) or []
        else:
            meeting_ids = list(map(int, db_user.get("group_$_ids", []))) or []
        meeting_collection = Collection("meeting")
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
                committee_id := self.datastore.additional_relation_models.get(
                    FullQualifiedId(meeting_collection, meeting_id), {}
                ).get("committee_id")
            )
        )
        new_committees_ids.update(committee_ids)
        added_ids = (
            new_committees_ids - db_committee_ids - detected_deleted_committee_ids
        )
        removed_ids = (
            db_committee_ids - new_committees_ids - detected_deleted_committee_ids
        )

        if not added_ids and not removed_ids:
            return {}

        fqfield_user = FullQualifiedField(Collection("user"), user_id, "committee_ids")
        relation_el: ListUpdateElement = {
            "type": "list_update",
            "add": [int(x) for x in added_ids],
            "remove": [int(x) for x in removed_ids],
        }
        relation_update: RelationUpdates = {fqfield_user: relation_el}

        def add_relation(add: bool, set_: Set[int]) -> None:
            for committee_id in set_:
                fqfield_committee = FullQualifiedField(
                    Collection("committee"), committee_id, "user_ids"
                )

                relation_update[fqfield_committee] = {
                    "type": "list_update",
                    "add": [user_id] if add else cast(List[int], []),
                    "remove": [] if add else [user_id],
                }

        add_relation(True, added_ids)
        add_relation(False, removed_ids)
        return relation_update
