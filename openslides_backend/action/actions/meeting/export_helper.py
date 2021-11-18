from typing import Any, Dict, List

from datastore.shared.util import is_reserved_field

from ....models.base import model_registry
from ....services.datastore.interface import DatastoreService
from ....services.media.interface import MediaService
from ....shared.filters import FilterOperator
from ....shared.patterns import Collection, FullQualifiedId


def export_meeting(
    datastore: DatastoreService, media: MediaService, meeting_id: int
) -> Dict[str, Any]:
    export = {}

    # handle collections with meeting_id
    meeting_collections = get_collections_with_meeting_id()
    for collection in meeting_collections:
        res = datastore.filter(
            Collection(collection),
            FilterOperator("meeting_id", "=", meeting_id),
        )
        export[collection] = add_empty_fields(
            remove_meta_fields(list(res.values())), collection
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
        "mediafile",
        "projector",
        "projection",
        "projector_message",
        "projector_countdown",
        "chat_group",
        "chat_message",
    ]
    return collections


def remove_meta_fields(res: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    list_without_meta_fields = []
    for entry in res:
        new_entry = {}
        for fieldname in entry:
            if not is_reserved_field(fieldname):
                new_entry[fieldname] = entry[fieldname]
        list_without_meta_fields.append(new_entry)
    return list_without_meta_fields


def add_empty_fields(
    res: List[Dict[str, Any]], collection: str
) -> List[Dict[str, Any]]:
    fields = set(
        field.get_own_field_name()
        for field in model_registry[Collection(collection)]().get_fields()
    )
    for entry in res:
        for field in fields:
            if field not in entry:
                entry[field] = None
    return res
