from typing import Any, Dict, List

from datastore.shared.util import is_reserved_field

from ....models.base import model_registry
from ....services.datastore.interface import DatastoreService
from ....shared.filters import FilterOperator
from ....shared.patterns import Collection, FullQualifiedId


def export_meeting(datastore: DatastoreService, meeting_id: int) -> Dict[str, Any]:
    export = {}

    # handle collections with meeting_id
    meeting_collections = get_collections_with_meeting_id()
    for collection in meeting_collections:
        res = datastore.filter(
            Collection(collection),
            FilterOperator("meeting_id", "=", meeting_id),
        )
        export[collection] = add_empty_fields(
            remove_meta_fields(transfer_keys(res)), collection
        )

    # handle meeting
    meeting = datastore.get(FullQualifiedId(Collection("meeting"), meeting_id))
    export["meeting"] = add_empty_fields(
        remove_meta_fields(transfer_keys({meeting_id: meeting})), "meeting"
    )

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
        "mediafile",
        "projector",
        "projection",
        "projector_message",
        "projector_countdown",
        "chat_group",
        "chat_message",
    ]
    return collections


def transfer_keys(res: Dict[int, Any]) -> Dict[str, Any]:
    new_dict = {}
    for key in res:
        new_dict[str(key)] = res[key]
    return new_dict


def remove_meta_fields(res: Dict[str, Any]) -> Dict[str, Any]:
    dict_without_meta_fields = {}
    for key in res:
        new_entry = {}
        for fieldname in res[key]:
            if not is_reserved_field(fieldname):
                new_entry[fieldname] = res[key][fieldname]
        dict_without_meta_fields[str(key)] = new_entry
    return dict_without_meta_fields


def add_empty_fields(res: Dict[str, Any], collection: str) -> Dict[str, Any]:
    fields = set(
        field.get_own_field_name()
        for field in model_registry[Collection(collection)]().get_fields()
    )
    for key in res:
        for field in fields:
            if field not in res[key]:
                res[key][field] = None
    return res
