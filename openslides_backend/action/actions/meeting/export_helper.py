from typing import Any, Dict, Iterable

from datastore.shared.util import is_reserved_field

from migrations import get_backend_migration_index

from ....models.fields import OnDelete, RelationListField
from ....models.models import Meeting
from ....services.datastore.commands import GetManyRequest
from ....services.datastore.interface import DatastoreService
from ....shared.patterns import fqid_from_collection_and_id


def export_meeting(datastore: DatastoreService, meeting_id: int) -> Dict[str, Any]:
    export: Dict[str, Any] = {}

    # fetch meeting
    meeting = datastore.get(
        fqid_from_collection_and_id("meeting", meeting_id),
        [],
        lock_result=False,
        use_changed_models=False,
    )
    export["meeting"] = remove_meta_fields(transfer_keys({meeting_id: meeting}))
    export["_migration_index"] = get_backend_migration_index()

    # fetch related models
    relation_fields = list(get_relation_fields())
    get_many_requests = [
        GetManyRequest(field.get_target_collection(), ids)
        for field in relation_fields
        if (ids := meeting.get(field.get_own_field_name()))
    ]
    if get_many_requests:
        results = datastore.get_many(
            get_many_requests, lock_result=False, use_changed_models=False
        )
    else:
        results = {}

    for field in relation_fields:
        collection = field.get_target_collection()
        if collection in results:
            export[str(collection)] = remove_meta_fields(
                transfer_keys(results[collection])
            )
        else:
            export[str(collection)] = {}

    if meeting.get("user_ids"):
        get_many_request = GetManyRequest("user", meeting["user_ids"])
        users = datastore.get_many(
            [get_many_request], lock_result=False, use_changed_models=False
        )
        export["user"] = remove_meta_fields(transfer_keys(users["user"]))

    return export


def remove_meta_fields(res: Dict[str, Any]) -> Dict[str, Any]:
    dict_without_meta_fields = {}
    for key in res:
        new_entry = {}
        for fieldname in res[key]:
            if not is_reserved_field(fieldname):
                new_entry[fieldname] = res[key][fieldname]
        dict_without_meta_fields[str(key)] = new_entry
    return dict_without_meta_fields


def get_relation_fields() -> Iterable[RelationListField]:
    for field in Meeting().get_relation_fields():
        if (
            isinstance(field, RelationListField)
            and field.on_delete == OnDelete.CASCADE
            and field.get_own_field_name().endswith("_ids")
        ):
            yield field


def transfer_keys(res: Dict[int, Any]) -> Dict[str, Any]:
    new_dict = {}
    for key in res:
        new_dict[str(key)] = res[key]
    return new_dict
