from typing import Any, Dict, List, Set, cast

from openslides_backend.models.models import User
from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.services.datastore.interface import InstanceAdditionalBehaviour

from ...models.fields import Field
from ...shared.patterns import Collection, FullQualifiedField, FullQualifiedId
from .calculated_field_handler import CalculatedFieldHandler
from .typing import ListUpdateElement, RelationUpdates


class UserCommitteeCalculateHandler(CalculatedFieldHandler):
    """
    CalculatedFieldHandler to fill the user.committee_ids and the related committee.user_ids
    by catching modifications of User.group_$_ids and User.committee__management_level.
    A user belongs to a committee, if he is member of a meeting in the committee via group or
    he has rights on CommitteeManagementLevel.
    """

    def process_field(
        self, field: Field, field_name: str, instance: Dict[str, Any], action: str
    ) -> RelationUpdates:
        cml_fields = get_field_list_from_template(
            cast(List[str], User.committee__management_level.replacement_enum),
            "committee_$%s_management_level",
        )
        if (
            field.own_collection.collection != "user"
            or field_name not in ["group_$_ids", *cml_fields]
            or ("group_$_ids" in instance and field_name != "group_$_ids")
        ):
            return {}
        user_id = instance["id"]
        fqid = FullQualifiedId(field.own_collection, instance["id"])
        db_user = self.datastore.fetch_model(
            fqid,
            ["committee_ids", "group_$_ids", *cml_fields],
            db_additional_relevance=InstanceAdditionalBehaviour.ONLY_DBINST,
            exception=False,
        )
        db_committee_ids = set(db_user.get("committee_ids", []) or [])
        if any(cml_field in instance for cml_field in cml_fields):
            new_committees_ids = get_set_of_values_from_dict(instance, cml_fields)
        else:
            new_committees_ids = get_set_of_values_from_dict(db_user, cml_fields)
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
        added_ids = new_committees_ids - db_committee_ids
        removed_ids = db_committee_ids - new_committees_ids

        if not added_ids and not removed_ids:
            return {}

        relation_update: RelationUpdates = {}
        if not action == "user.delete":
            fqfield_user = FullQualifiedField(
                Collection("user"), user_id, "committee_ids"
            )
            relation_el: ListUpdateElement = {
                "type": "list_update",
                "add": [int(x) for x in added_ids],
                "remove": [int(x) for x in removed_ids],
            }
            relation_update[fqfield_user] = relation_el

        def add_relation(add: bool, set_: Set[int]) -> None:
            for committee_id in set_:
                fqfield_committee = FullQualifiedField(
                    Collection("committee"), committee_id, "user_ids"
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


def get_field_list_from_template(
    management_levels: List[str], template: str
) -> List[str]:
    return [template % management_level for management_level in management_levels]


def get_set_of_values_from_dict(
    instance: Dict[str, Any], management_levels: List[str], template: str = None
) -> Set[int]:
    if template:
        cml_fields = get_field_list_from_template(management_levels, template)
    else:
        cml_fields = management_levels
    return set(
        [
            committee_id
            for cml_field in cml_fields
            for committee_id in (instance.get(cml_field, []) or [])
        ]
    )
