from typing import Any, Dict, List

from datastore.shared.util import is_reserved_field

from ....models.base import model_registry
from ....models.fields import RelationListField
from ....models.models import Meeting
from ....services.datastore.commands import GetManyRequest
from ....services.datastore.interface import DatastoreService
from ....shared.patterns import Collection, FullQualifiedId


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
    relation_fields = get_relation_fields()
    get_many_requests = [
        GetManyRequest(field.get_target_collection(), ids)
        for field in relation_fields
        if (ids := meeting.get(field.get_own_field_name()))
    ]
    results = datastore.get_many(get_many_requests, use_changed_models=False)
    for field in relation_fields:
        collection = field.get_target_collection()
        if collection in results:
            export[str(collection)] = add_empty_fields(
                remove_meta_fields(transfer_keys(results[collection])), collection
            )
        else:
            export[str(collection)] = []

    return export


def get_relation_fields() -> List[RelationListField]:
    return [
        Meeting.group_ids,
        Meeting.personal_note_ids,
        Meeting.tag_ids,
        Meeting.agenda_item_ids,
        Meeting.list_of_speakers_ids,
        Meeting.speaker_ids,
        Meeting.topic_ids,
        Meeting.motion_ids,
        Meeting.motion_submitter_ids,
        Meeting.motion_comment_ids,
        Meeting.motion_comment_section_ids,
        Meeting.motion_category_ids,
        Meeting.motion_block_ids,
        Meeting.motion_change_recommendation_ids,
        Meeting.motion_state_ids,
        Meeting.motion_state_ids,
        Meeting.motion_workflow_ids,
        Meeting.motion_statute_paragraph_ids,
        Meeting.poll_ids,
        Meeting.option_ids,
        Meeting.vote_ids,
        Meeting.assignment_ids,
        Meeting.assignment_candidate_ids,
        Meeting.mediafile_ids,
        Meeting.projector_ids,
        Meeting.projection_ids,
        Meeting.projector_message_ids,
        Meeting.projector_countdown_ids,
        Meeting.chat_group_ids,
        Meeting.chat_message_ids,
    ]


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
        for field in model_registry[collection]().get_fields()
    )
    for key in res:
        for field in fields:
            if field not in res[key]:
                res[key][field] = None
    return res
