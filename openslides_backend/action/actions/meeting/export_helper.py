from typing import Any, Dict, Iterable, List

from datastore.shared.util import is_reserved_field

from openslides_backend.migrations import get_backend_migration_index

from ....models.base import model_registry
from ....models.fields import (
    BaseRelationField,
    GenericRelationField,
    OnDelete,
    RelationField,
    RelationListField,
    TemplateCharField,
    TemplateDecimalField,
    TemplateHTMLStrictField,
    TemplateRelationField,
    TemplateRelationListField,
)
from ....models.models import Meeting, User
from ....services.datastore.commands import GetManyRequest
from ....services.datastore.interface import DatastoreService
from ....shared.patterns import (
    collection_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)

FORBIDDEN_FIELDS = ["forwarded_motion_ids"]


def export_meeting(datastore: DatastoreService, meeting_id: int) -> Dict[str, Any]:
    export: Dict[str, Any] = {}

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
                    set(
                        entry.get(user_field.get_own_field_name())
                        for entry in export[collection].values()
                        if entry.get(user_field.get_own_field_name())
                    )
                )
            if (
                isinstance(user_field, RelationListField)
                and user_field.get_target_collection() == "user"
            ):
                for entry in export[collection].values():
                    if entry.get(user_field.get_own_field_name()):
                        user_ids.update(
                            set(
                                id_
                                for id_ in entry.get(user_field.get_own_field_name())
                                or []
                            )
                        )
            if isinstance(user_field, GenericRelationField):
                for entry in export[collection].values():
                    field_name = user_field.get_own_field_name()
                    if (
                        entry.get(field_name)
                        and collection_from_fqid(entry[field_name]) == "user"
                    ):
                        user_ids.add(id_from_fqid(entry[field_name]))
    add_users(list(user_ids), export, meeting_id, datastore)
    return export


def add_users(
    user_ids: List[int],
    export_data: Dict[str, Any],
    meeting_id: int,
    datastore: DatastoreService,
) -> None:
    if not user_ids:
        return
    fields = []
    template_fields = []
    for field in User().get_fields():
        if isinstance(
            field,
            (
                TemplateCharField,
                TemplateHTMLStrictField,
                TemplateDecimalField,
                TemplateRelationField,
                TemplateRelationListField,
            ),
        ):
            template_fields.append(
                (
                    struct_field := field.get_structured_field_name(meeting_id),
                    field.get_template_field_name(),
                )
            )
            fields.append(struct_field)
        else:
            fields.append(field.own_field_name)

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
        for field_name, field_template_name in template_fields:
            if user.get(field_name):
                user[field_template_name] = [str(meeting_id)]
        user["meeting_ids"] = [meeting_id]
        if meeting_id in (user.get("is_present_in_meeting_ids") or []):
            user["is_present_in_meeting_ids"] = [meeting_id]
        else:
            user["is_present_in_meeting_ids"] = None

    export_data["user"] = users


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
