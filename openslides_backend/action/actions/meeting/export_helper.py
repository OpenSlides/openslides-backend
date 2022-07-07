import struct
from ....models.models import User
from ....models.fields import (
    TemplateCharField,
    TemplateDecimalField,
    TemplateHTMLStrictField,
    TemplateRelationListField,
)



from typing import Any, Dict, Iterable

from datastore.shared.util import is_reserved_field

from openslides_backend.migrations import get_backend_migration_index

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


    add_users(meeting.get("user_ids"), export, meeting_id, datastore)
    #if meeting.get("user_ids"):
        # get_many_request = GetManyRequest("user", meeting["user_ids"])
        # users = datastore.get_many(
        #     [get_many_request], lock_result=False, use_changed_models=False
        # )
        # export["user"] = remove_meta_fields(transfer_keys(users["user"]))

    return export

def add_users(user_ids, export_data: Dict[str, Any], meeting_id: int, datastore: DatastoreService) -> None:
    if not user_ids:
        return
    fields = []
    template_fields =  []
    for field in User().get_fields():
        if isinstance(
            field,
            (
                TemplateCharField,
                TemplateHTMLStrictField,
                TemplateDecimalField,
                TemplateRelationListField,
            ),
        ):
            template_fields.append(
                (
                    struct_field:=field.get_structured_field_name(meeting_id),
                    field.get_template_field_name(),
                )
            )
            fields.append(struct_field)
        else:
            try:
                fields.append(field.own_field_name)
            except Exception as e:
                x = 5

    gmr = GetManyRequest(
        "user",
        user_ids,
        fields,
    )
    users = remove_meta_fields(
                transfer_keys(datastore.get_many(
        [gmr], lock_result=False, use_changed_models=False
    )["user"]))

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

def add_usersV1(user_ids, export_data: Dict[str, Any], meeting_id: int, datastore: DatastoreService) -> None:
    if not user_ids:
        return
    fields = []
    for field in User().get_fields():
        if isinstance(
            field,
            (
                TemplateCharField,
                TemplateHTMLStrictField,
                TemplateDecimalField,
                TemplateRelationListField,
            ),
        ):
            fields.append(
                (
                    field.get_structured_field_name(meeting_id),
                    field.get_template_field_name(),
                )
            )

    gmr = GetManyRequest(
        "user",
        user_ids,
        [
            "id",
            "username",
            "pronoun",
            "title",
            "first_name",
            "last_name",
            "is_active",
            "is_physical_person",
            "password",
            "default",
            "can_change_own_password",
            "gender",
            "email",
            "default_number",
            "default_structure_level",
            "default_vote_weight",
            "last_email_send",
            "is_demo_user",
            "organization_management_level",
            "is_present_in_meeting_ids",
        ]
        + [field_pair[0] for field_pair in fields],
    )
    users = remove_meta_fields(
                transfer_keys(datastore.get_many(
        [gmr], lock_result=False, use_changed_models=False
    )["user"]))

    for user in users.values():
        for field_name, field_template_name in fields:
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
