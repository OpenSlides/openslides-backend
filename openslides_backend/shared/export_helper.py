from collections.abc import Iterable
from typing import Any

from openslides_backend.datastore.shared.util import is_reserved_field
from openslides_backend.migrations import get_backend_migration_index

from ..models.base import model_registry
from ..models.fields import (
    BaseRelationField,
    GenericRelationField,
    OnDelete,
    RelationField,
    RelationListField,
)
from ..models.models import Meeting, User
from ..services.datastore.commands import GetManyRequest
from ..services.datastore.interface import DatastoreService
from .patterns import collection_from_fqid, fqid_from_collection_and_id, id_from_fqid

FORBIDDEN_FIELDS = ["forwarded_motion_ids"]


def export_meeting(datastore: DatastoreService, meeting_id: int) -> dict[str, Any]:
    export: dict[str, Any] = {}

    # fetch meeting
    meeting = datastore.get(
        fqid_from_collection_and_id("meeting", meeting_id),
        [],
        lock_result=False,
        use_changed_models=False,
    )
    for forbidden_field in FORBIDDEN_FIELDS:
        meeting.pop(forbidden_field, None)

    export["meeting"] = remove_meta_fields(transfer_keys({meeting_id: meeting}))
    export["_migration_index"] = get_backend_migration_index()

    # initialize user_ids
    user_ids = set(meeting.get("user_ids", []))

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

    # update user_ids
    for collection in export:
        if collection == "_migration_index":
            continue
        model = model_registry[collection]()
        user_fields: Iterable[BaseRelationField] = model.get_relation_fields()
        for user_field in user_fields:
            if (
                isinstance(user_field, RelationField)
                and user_field.get_target_collection() == "user"
            ):
                user_ids.update(
                    {
                        entry.get(user_field.get_own_field_name())
                        for entry in export[collection].values()
                        if entry.get(user_field.get_own_field_name())
                    }
                )
            if (
                isinstance(user_field, RelationListField)
                and user_field.get_target_collection() == "user"
            ):
                for entry in export[collection].values():
                    if entry.get(user_field.get_own_field_name()):
                        user_ids.update(
                            {
                                id_
                                for id_ in entry.get(user_field.get_own_field_name())
                                or []
                            }
                        )
            if (
                isinstance(user_field, RelationField)
                and user_field.get_target_collection() == "meeting_user"
            ):
                id_ = entry.get(user_field.get_own_field_name())
                if id_:
                    user_ids.add(results["meeting_user"][id_]["user_id"])

            if (
                isinstance(user_field, RelationListField)
                and user_field.get_target_collection() == "meeting_user"
            ):
                for entry in export[collection].values():
                    if entry.get(user_field.get_own_field_name()):
                        user_ids.update(
                            {
                                user_id
                                for id_ in entry.get(user_field.get_own_field_name())
                                if (
                                    user_id := results["meeting_user"][id_].get(
                                        "user_id"
                                    )
                                )
                            }
                        )
            if isinstance(user_field, GenericRelationField):
                for entry in export[collection].values():
                    field_name = user_field.get_own_field_name()
                    if not entry.get(field_name):
                        continue
                    if collection_from_fqid(entry[field_name]) == "user":
                        user_ids.add(id_from_fqid(entry[field_name]))
                    elif collection_from_fqid(entry[field_name]) == "meeting_user":
                        id_ = id_from_fqid(entry[field_name])
                        user_ids.add(results["meeting_user"][id_]["user_id"])
    add_users(list(user_ids), export, meeting_id, datastore)
    return export


def add_users(
    user_ids: list[int],
    export_data: dict[str, Any],
    meeting_id: int,
    datastore: DatastoreService,
) -> None:
    if not user_ids:
        return
    fields = [field.own_field_name for field in User().get_fields()]

    gmr = GetManyRequest(
        "user",
        user_ids,
        fields,
    )
    users = remove_meta_fields(
        transfer_keys(
            datastore.get_many([gmr], lock_result=False, use_changed_models=False)[
                "user"
            ]
        )
    )

    for user in users.values():
        user["meeting_ids"] = [meeting_id]
        if meeting_id in (user.get("is_present_in_meeting_ids") or []):
            user["is_present_in_meeting_ids"] = [meeting_id]
        else:
            user["is_present_in_meeting_ids"] = None
        # limit user fields to exported objects
        collection_field_tupels = [
            ("meeting_user", "meeting_user_ids"),
            ("poll", "poll_voted_ids"),
            ("option", "option_ids"),
            ("vote", "vote_ids"),
            ("poll_candidate", "poll_candidate_ids"),
            ("vote", "delegated_vote_ids"),
        ]
        for collection, fname in collection_field_tupels:
            user[fname] = [
                id_
                for id_ in user.get(fname, [])
                if export_data.get(collection, {}).get(str(id_))
            ]

    export_data["user"] = users


def remove_meta_fields(res: dict[str, Any]) -> dict[str, Any]:
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


def transfer_keys(res: dict[int, Any]) -> dict[str, Any]:
    new_dict = {}
    for key in res:
        new_dict[str(key)] = res[key]
    return new_dict
