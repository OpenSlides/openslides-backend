from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union

from datastore.migrations import BaseModelMigration, MigrationException
from datastore.shared.typing import JSON
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import (
    BaseRequestEvent,
    RequestDeleteEvent,
    RequestUpdateEvent,
)

from openslides_backend.shared.patterns import collection_and_id_from_fqid

FieldTargetRemoveType = Tuple[
    str, Union[str, List[str]], Union[str, List["FieldTargetRemoveType"]]
]

ListUpdatesDict = Dict[str, List[Union[str, int]]]
ListFieldsData = TypedDict(
    "ListFieldsData",
    {"add": ListUpdatesDict, "remove": ListUpdatesDict},
    total=False,
)


class Migration(BaseModelMigration):
    """
    This migration deletes all meeting users that don't have group_ids, as that is what the update function will do as well from now on.
    """

    target_migration_index = 50
    field_target_relation_list: List[FieldTargetRemoveType] = [
        ("assignment_candidate_ids", "assignment_candidate", "meeting_user_id"),
        ("chat_message_ids", "chat_message", "meeting_user_id"),
        ("meeting_id", "meeting", "meeting_user_ids"),
        (
            "motion_submitter_ids",
            "motion_submitter",
            [
                ("meeting_id", "meeting", "motion_submitter_ids"),
                ("motion_id", "motion", "submitter_ids"),
            ],
        ),  # CASCADE
        (
            "personal_note_ids",
            "personal_note",
            [
                ("content_object_id", ["motion"], "personal_note_ids"),  # GENERIC
                ("meeting_id", "meeting", "personal_note_ids"),
            ],
        ),  # CASCADE
        ("speaker_ids", "speaker", "meeting_user_id"),
        ("supported_motion_ids", "motion", "supporter_meeting_user_ids"),
        ("user_id", "user", "meeting_user_ids"),
        ("vote_delegated_to_id", "meeting_user", "vote_delegations_from_ids"),
        ("vote_delegations_from_ids", "meeting_user", "vote_delegated_to_id"),
    ]
    remove_events: Dict[str, BaseRequestEvent]
    additional_events: Dict[str, Tuple[Dict[str, JSON], ListFieldsData]]

    def migrate_models(self) -> Optional[List[BaseRequestEvent]]:
        db_models = self.reader.get_all("meeting_user")
        to_be_deleted = {
            id_: meeting_user
            for id_, meeting_user in db_models.items()
            if len(meeting_user.get("group_ids", [])) == 0
        }
        self.remove_events = {
            f"meeting_user/{id_}": RequestDeleteEvent(
                fqid_from_collection_and_id("meeting_user", id_),
            )
            for id_ in to_be_deleted.keys()
        }
        self.additional_events = defaultdict()
        for id_, meeting_user in to_be_deleted.items():
            self.add_relation_migration_events(
                id_, meeting_user, self.field_target_relation_list
            )
        additional = [
            RequestUpdateEvent(fqid, fields, list_fields)
            for fqid, (fields, list_fields) in self.additional_events.items()
        ]
        return [*additional, *self.remove_events.values()]

    def add_relation_migration_events(
        self,
        remove_id: int,
        remove_model: Any,
        instructions: List[FieldTargetRemoveType],
    ) -> None:
        for field, collection, to_empty in instructions:
            target_ids = remove_model.get(field)
            if target_ids:
                if isinstance(target_ids, int) or isinstance(target_ids, str):
                    if isinstance(target_ids, str):  # GENERICS
                        collection, target_ids = collection_and_id_from_fqid(target_ids)
                    elif not isinstance(collection, str):
                        raise MigrationException(
                            f"Couldn't resolve generic field {field}, value '{target_ids}' was not an fqid"
                        )
                    self.add_relation_migration_events_helper(
                        collection, target_ids, to_empty, remove_id
                    )
                elif isinstance(target_ids, list):  # list
                    for target_date in target_ids:
                        if isinstance(target_date, int) or isinstance(target_date, str):
                            if isinstance(target_date, str):  # GENERICS
                                collection, target_date = collection_and_id_from_fqid(
                                    target_date
                                )
                            elif not isinstance(collection, str):
                                raise MigrationException(
                                    f"Couldn't resolve generic field {field}, value '{target_ids}' was not an fqid"
                                )
                            self.add_relation_migration_events_helper(
                                collection, target_date, to_empty, remove_id
                            )
                        else:
                            raise MigrationException(
                                f"Couldn't resolve field {field} as id field, value: '{target_ids}'"
                            )
                else:
                    raise MigrationException(
                        f"Couldn't resolve field {field} as id field, value: '{target_ids}'"
                    )

    def add_relation_migration_events_helper(
        self,
        collection: str,
        model_id: int,
        to_empty: Union[str, List["FieldTargetRemoveType"]],
        remove_id: int,
    ) -> None:
        fqid = fqid_from_collection_and_id(collection, model_id)
        if not self.remove_events.get(fqid):
            if isinstance(to_empty, str):
                is_list = to_empty.endswith("_ids")
                if prior_event := self.additional_events.get(fqid):
                    if is_list:
                        if remove := prior_event[1].get("remove"):
                            if prior_empty_values := remove.get(to_empty):
                                remove[to_empty] = list(
                                    set([*prior_empty_values, remove_id])
                                )
                            else:
                                remove[to_empty] = [remove_id]
                        else:
                            prior_event[1]["remove"] = {to_empty: [remove_id]}
                    else:
                        prior_event[0][to_empty] = None
                else:
                    if is_list:
                        self.additional_events[fqid] = (
                            {},
                            {"remove": {to_empty: [remove_id]}},
                        )
                    else:
                        self.additional_events[fqid] = ({to_empty: None}, {})
            else:
                if self.additional_events.get(fqid):
                    del self.additional_events[fqid]
                self.remove_events[fqid] = RequestDeleteEvent(fqid)
                model = self.reader.get(fqid)
                self.add_relation_migration_events(model_id, model, to_empty)
