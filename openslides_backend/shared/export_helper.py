from collections.abc import Iterable
from typing import Any

from datastore.shared.util import is_reserved_field

from openslides_backend.migrations import get_backend_migration_index
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID

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

NON_CASCADING_MEETING_RELATION_LISTS = ["poll_candidate_list_ids", "poll_candidate_ids"]

HISTORY_FIELDS_PER_COLLECTION = {
    "meeting": ["relevant_history_entry_ids"],
    "user": ["history_entry_ids", "history_position_ids"],
    **{collection: ["history_entry_ids"] for collection in ["motion", "assignment"]},
}


def export_meeting(
    datastore: DatastoreService,
    meeting_id: int,
    internal_target: bool = False,
    update_mediafiles: bool = False,
) -> dict[str, Any]:
    export: dict[str, Any] = {}

    # fetch meeting
    meeting = datastore.get(
        fqid_from_collection_and_id("meeting", meeting_id),
        [],
        lock_result=False,
        use_changed_models=False,
    )
    for forbidden_field in FORBIDDEN_FIELDS + HISTORY_FIELDS_PER_COLLECTION["meeting"]:
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
        # update_mediafiles_for_internal_calls
        if update_mediafiles and len(
            mediafile_ids := results.get("mediafile", {}).keys()
        ) != len(meeting_mediafiles := results.get("meeting_mediafile", {})):
            mm_with_unknown_mediafiles = {
                mm_id: mm_data
                for mm_id, mm_data in meeting_mediafiles.items()
                if mm_data["mediafile_id"] not in mediafile_ids
            }
            unknown_mediafiles = datastore.get_many(
                [
                    GetManyRequest(
                        "mediafile",
                        [
                            mm["mediafile_id"]
                            for mm in mm_with_unknown_mediafiles.values()
                        ],
                        [
                            "id",
                            "owner_id",
                            "meeting_mediafile_ids",
                            "published_to_meetings_in_organization_id",
                        ],
                    ),
                ],
                use_changed_models=False,
            )["mediafile"]
            for mm_id, mm_data in mm_with_unknown_mediafiles.items():
                mediafile_id = mm_data["mediafile_id"]
                mediafile = unknown_mediafiles.get(mediafile_id)
                if (
                    mediafile
                    and mediafile["owner_id"] == ONE_ORGANIZATION_FQID
                    and mediafile["published_to_meetings_in_organization_id"]
                    == ONE_ORGANIZATION_ID
                ):
                    mediafile["meeting_mediafile_ids"] = [mm_id]
                    results.setdefault("mediafile", {})[mediafile_id] = mediafile

    else:
        results = {}

    for field in relation_fields:
        collection = field.get_target_collection()
        if collection in results:
            export[str(collection)] = remove_history_fields(
                collection, remove_meta_fields(transfer_keys(results[collection]))
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
    add_users(list(user_ids), export, meeting_id, datastore, internal_target)
    return export


def add_users(
    user_ids: list[int],
    export_data: dict[str, Any],
    meeting_id: int,
    datastore: DatastoreService,
    internal_target: bool,
) -> None:
    if not user_ids:
        return
    fields = [field.own_field_name for field in User().get_fields()]

    gmr = GetManyRequest(
        "user",
        user_ids,
        fields,
    )
    users = remove_history_fields(
        "user",
        remove_meta_fields(
            transfer_keys(
                datastore.get_many([gmr], lock_result=False, use_changed_models=False)[
                    "user"
                ]
            )
        ),
    )

    for user in users.values():
        user["meeting_ids"] = [meeting_id]
        if meeting_id in (user.get("is_present_in_meeting_ids") or []):
            user["is_present_in_meeting_ids"] = [meeting_id]
        else:
            user["is_present_in_meeting_ids"] = None
        if not internal_target and (gender_id := user.pop("gender_id", None)):
            gender_dict = datastore.get_all("gender", ["name"], lock_result=False)
            user["gender"] = gender_dict.get(gender_id, {}).get("name")
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


def remove_history_fields(collection: str, res: dict[str, Any]) -> dict[str, Any]:
    for field in HISTORY_FIELDS_PER_COLLECTION.get(collection, []):
        for key in res:
            res[key].pop(field, None)
    return res


def get_relation_fields() -> Iterable[RelationListField]:
    for field in Meeting().get_relation_fields():
        if (
            isinstance(field, RelationListField)
            and field not in HISTORY_FIELDS_PER_COLLECTION["meeting"]
            and (
                (
                    field.on_delete == OnDelete.CASCADE
                    and field.get_own_field_name().endswith("_ids")
                )
                or field.get_own_field_name() in NON_CASCADING_MEETING_RELATION_LISTS
            )
        ):
            yield field


def transfer_keys(res: dict[int, Any]) -> dict[str, Any]:
    new_dict = {}
    for key in res:
        new_dict[str(key)] = res[key]
    return new_dict
