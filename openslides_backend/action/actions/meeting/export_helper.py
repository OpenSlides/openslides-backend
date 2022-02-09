from typing import Any, Dict, Iterable

from datastore.shared.util import is_reserved_field

from ....models.base import model_registry
from ....models.fields import OnDelete, RelationListField
from ....models.models import Meeting
from ....services.datastore.commands import GetManyRequest
from ....services.datastore.interface import DatastoreService
from ....shared.patterns import Collection, FullQualifiedId
from ....services.media.interface import MediaService
from ....shared.filters import FilterOperator
from ....shared.patterns import KEYSEPARATOR, Collection, FullQualifiedId


def export_meeting(datastore: DatastoreService, meeting_id: int) -> Dict[str, Any]:
    export = {}
    # fetch meeting
    meeting = datastore.get(
        FullQualifiedId(Collection("meeting"), meeting_id), [], use_changed_models=False
    )
    export["meeting"] = add_empty_fields(
        remove_meta_fields(transfer_keys({meeting_id: meeting})), Collection("meeting")
    )
    # fetch related models
    relation_fields = list(get_relation_fields())
    get_many_requests = [
        GetManyRequest(field.get_target_collection(), ids)
        for field in relation_fields
        if (ids := meeting.get(field.get_own_field_name()))
    ]
    if get_many_requests:
        results = datastore.get_many(get_many_requests, use_changed_models=False)
    else:
        results = {}

    for field in relation_fields:
        collection = field.get_target_collection()
        if collection in results:
            export[str(collection)] = add_empty_fields(
                remove_meta_fields(transfer_keys(results[collection])), collection
            )
        else:
            export[str(collection)] = {}

    # handle mediafiles
    res = datastore.filter(
        Collection("mediafile"),
        FilterOperator("owner_id", "=", "meeting" + KEYSEPARATOR + str(meeting_id)),
    )
    export["mediafile"] = add_empty_fields(
        remove_meta_fields(list(res.values())), "mediafile"
    )

    # handle meeting
    meeting = datastore.get(FullQualifiedId(Collection("meeting"), meeting_id))
    export["meeting"] = add_empty_fields(remove_meta_fields([meeting]), "meeting")
    return export


def get_collections_with_meeting_id() -> List[str]:
    collections = [
        "group",
        "personal_note",
        "tag",
        "agenda_item",
        "list_of_speakers",
        "speaker",
        "topic",
        "motion",
        "motion_submitter",
        "motion_comment",
        "motion_comment_section",
        "motion_category",
        "motion_block",
        "motion_change_recommendation",
        "motion_state",
        "motion_workflow",
        "motion_statute_paragraph",
        "poll",
        "option",
        "vote",
        "assignment",
        "assignment_candidate",
        "projector",
        "projection",
        "projector_message",
        "projector_countdown",
        "chat_group",
        "chat_message",
    ]
    return collections


def remove_meta_fields(res: Dict[str, Any]) -> Dict[str, Any]:
    dict_without_meta_fields = {}
    for key in res:
        new_entry = {}
        for fieldname in res[key]:
            if not is_reserved_field(fieldname):
                new_entry[fieldname] = res[key][fieldname]
        dict_without_meta_fields[str(key)] = new_entry
    return dict_without_meta_fields


def add_empty_fields(res: Dict[str, Any], collection: Collection) -> Dict[str, Any]:
    fields = set(
        field.get_own_field_name()
        for field in model_registry[collection]().get_fields()
    )
    for key in res:
        for field in fields:
            if field not in res[key]:
                res[key][field] = None
    return res

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
