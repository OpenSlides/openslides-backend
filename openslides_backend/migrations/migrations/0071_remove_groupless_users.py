from collections import defaultdict
from enum import Enum, auto
from time import time
from typing import Any, Literal, TypedDict, cast

from datastore.migrations import BaseModelMigration
from datastore.reader.core import GetManyRequestPart
from datastore.writer.core.write_request import (
    BaseRequestEvent,
    RequestDeleteEvent,
    RequestUpdateEvent,
)

from ...shared.filters import And, FilterOperator, Or
from ...shared.patterns import collection_and_id_from_fqid, fqid_from_collection_and_id


class CountdownCommand(Enum):
    START = auto()
    STOP = auto()
    RESET = auto()
    RESTART = auto()


class MigrationDataField(TypedDict):
    to_collection: str
    to_field: str
    on_delete: Literal["cascade", "special"] | None


SPEAKER_EXTRA_FIELDS: list[str] = []

COLLECTION_TO_MIGRATION_FIELDS: dict[str, dict[str, MigrationDataField]] = {
    "meeting_user": {
        "user_id": {
            "to_collection": "user",
            "to_field": "meeting_user_ids",
            "on_delete": None,
        },
        "meeting_id": {
            "to_collection": "meeting",
            "to_field": "meeting_user_ids",
            "on_delete": None,
        },
        "personal_note_ids": {
            "to_collection": "personal_note",
            "to_field": "meeting_user_id",
            "on_delete": "cascade",
        },
        "speaker_ids": {
            "to_collection": "speaker",
            "to_field": "meeting_user_id",
            "on_delete": None,
        },
        "supported_motion_ids": {
            "to_collection": "motion",
            "to_field": "supporter_meeting_user_ids",
            "on_delete": None,
        },
        "motion_editor_ids": {
            "to_collection": "motion_editor",
            "to_field": "meeting_user_id",
            "on_delete": None,
        },
        "motion_working_group_speaker_ids": {
            "to_collection": "motion_working_group_speaker",
            "to_field": "meeting_user_id",
            "on_delete": None,
        },
        "motion_submitter_ids": {
            "to_collection": "motion_submitter",
            "to_field": "meeting_user_id",
            "on_delete": None,
        },
        "assignment_candidate_ids": {
            "to_collection": "assignment_candidate",
            "to_field": "meeting_user_id",
            "on_delete": None,
        },
        "vote_delegated_to_id": {
            "to_collection": "meeting_user",
            "to_field": "vote_delegations_from_ids",
            "on_delete": None,
        },
        "vote_delegations_from_ids": {
            "to_collection": "meeting_user",
            "to_field": "vote_delegated_to_id",
            "on_delete": None,
        },
        "chat_message_ids": {
            "to_collection": "chat_message",
            "to_field": "meeting_user_id",
            "on_delete": None,
        },
        # "group_ids": {
        #     "to_collection": "group",
        #     "to_field": "meeting_user_ids",
        #     "on_delete": None,
        # },
        "structure_level_ids": {
            "to_collection": "structure_level",
            "to_field": "meeting_user_ids",
            "on_delete": None,
        },
    },
    "speaker": {
        "list_of_speakers_id": {
            "to_collection": "list_of_speakers",
            "to_field": "speaker_ids",
            "on_delete": None,
        },
        "structure_level_list_of_speakers_id": {
            "to_collection": "structure_level_list_of_speakers",
            "to_field": "speaker_ids",
            "on_delete": None,
        },
        # "meeting_user_id": {
        #     "to_collection": "meeting_user",
        #     "to_field": "speaker_ids",
        #     "on_delete": None,
        # },
        "point_of_order_category_id": {
            "to_collection": "point_of_order_category",
            "to_field": "speaker_ids",
            "on_delete": None,
        },
        "meeting_id": {
            "to_collection": "meeting",
            "to_field": "speaker_ids",
            "on_delete": None,
        },
    },
    "personal_note": {
        # "meeting_user_id": {
        #     "to_collection": "meeting_user",
        #     "to_field": "personal_note_ids",
        #     "on_delete": None,
        # },
        "content_object_id": {
            "to_collection": "motion",
            "to_field": "personal_note_ids",
            "on_delete": "special",  # bc generic but only points to motion
        },
        "meeting_id": {
            "to_collection": "meeting",
            "to_field": "personal_note_ids",
            "on_delete": None,
        },
    },
}


def is_list_field(field: str) -> bool:
    return field.endswith("_ids")


# TODO: MEETING PRESENCE
# should be empty for all deleted musers bc it should've been
# automatically unset when the groups were removed.
# Check if it's possible that may not be the case.


class Migration(BaseModelMigration):
    """
    This migration removes meeting_users without groups
    """

    target_migration_index = 72

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        self.end_time = round(time())
        filter_ = And(
            Or(
                FilterOperator("group_ids", "=", None),
                FilterOperator("group_ids", "=", []),
            ),
            FilterOperator("meta_deleted", "!=", True),
        )
        musers_to_delete = self.reader.filter(
            "meeting_user",
            filter_,
            list(COLLECTION_TO_MIGRATION_FIELDS["meeting_user"]),
        )
        speaker_ids_to_delete, events = self.calculate_speakers_to_delete(
            musers_to_delete
        )
        self.collection_to_model_ids_to_delete: dict[str, set[int]] = defaultdict(set)
        self.collection_to_model_ids_to_delete["speaker"] = set(speaker_ids_to_delete)

        self.fqids_to_delete: set[str] = {
            f"meeting_user/{id_}" for id_ in musers_to_delete
        }
        self.fqids_to_delete.update({f"speaker/{id_}" for id_ in speaker_ids_to_delete})

        self.fqid_to_list_removal: dict[str, dict[str, list[int]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.fqid_to_empty_fields: dict[str, set[str]] = defaultdict(set)
        self.migrate_collection("meeting_user", musers_to_delete)
        while delete_collections := list(self.collection_to_model_ids_to_delete.keys()):
            delete_collection = delete_collections[0]
            delete_collection_ids = self.collection_to_model_ids_to_delete.pop(
                delete_collection, None
            )
            if delete_collection_ids:
                data_to_delete = self.reader.get_many(
                    [
                        GetManyRequestPart(
                            delete_collection,
                            list(delete_collection_ids),
                            list(COLLECTION_TO_MIGRATION_FIELDS[delete_collection]),
                        )
                    ]
                ).get(delete_collection, {})
                self.migrate_collection(delete_collection, data_to_delete)
        events.extend(
            [
                (
                    RequestDeleteEvent(fqid)
                    if fqid in self.fqids_to_delete
                    else RequestUpdateEvent(
                        fqid,
                        fields={
                            field: None
                            for field in self.fqid_to_empty_fields.get(fqid, [])
                        },
                        list_fields=(
                            {
                                "remove": {
                                    field: [val for val in lis]
                                    for field, lis in list_data.items()
                                }
                            }
                            if (list_data := self.fqid_to_list_removal.get(fqid, {}))
                            else {}
                        ),
                    )
                )
                for fqid in self.fqids_to_delete.union(
                    self.fqid_to_empty_fields, self.fqid_to_list_removal
                )
            ]
        )
        return events

    def migrate_collection(
        self, collection: str, models_to_delete: dict[int, dict[str, Any]]
    ) -> None:
        self.load_data(collection, models_to_delete)
        for id_, meeting_user in models_to_delete.items():
            for field, value in meeting_user.items():
                if field_data := COLLECTION_TO_MIGRATION_FIELDS[collection].get(field):
                    if is_list_field(field) and value:
                        for val_id in value:
                            self.handle_id(collection, id_, val_id, field, field_data)
                    elif value:
                        self.handle_id(collection, id_, value, field, field_data)

    def load_data(
        self, collection: str, models_to_delete: dict[int, dict[str, Any]]
    ) -> None:
        fields = COLLECTION_TO_MIGRATION_FIELDS[collection]
        collection_to_target_model_ids: dict[str, set[int]] = defaultdict(set)
        for field, field_data in fields.items():
            collection_to_target_model_ids[field_data["to_collection"]].update(
                [
                    id_ if isinstance(id_, int) else id_.split("/")[1]
                    for mod in models_to_delete.values()
                    for id_ in (mod.get(field) or [])
                ]
                if is_list_field(field)
                else [
                    id_ if isinstance(id_, int) else id_.split("/")[1]
                    for mod in models_to_delete.values()
                    if (id_ := mod.get(field))
                ]
            )
        self.existing_target_models = self.reader.get_many(
            [
                GetManyRequestPart(coll, list(ids), ["id"])
                for coll, ids in collection_to_target_model_ids.items()
            ]
        )

    def exists(self, fqid: str) -> bool:
        collection, id_ = collection_and_id_from_fqid(fqid)
        return id_ in self.existing_target_models.get(collection, {})

    def handle_id(
        self,
        base_collection: str,
        base_id: int,
        value_id: int | str,
        field: str,
        field_data: MigrationDataField,
    ) -> None:
        target_fqid = f"{field_data['to_collection']}/{value_id}"
        if target_fqid in self.fqids_to_delete:
            return
        match field_data["on_delete"]:
            case "special":
                if base_collection == "personal_note" and field == "content_object_id":
                    # back relation is always list-field personal_note_ids
                    assert isinstance(value_id, str)
                    target_fqid = value_id
                    if target_fqid in self.fqids_to_delete or not self.exists(
                        target_fqid
                    ):
                        return
                    self.fqid_to_list_removal[target_fqid]["personal_note_ids"].append(
                        base_id
                    )
                else:
                    raise Exception(
                        f"Bad migration: Handling of {base_collection}/{field} not defined."
                    )
            case "cascade":
                if not self.exists(target_fqid):
                    return
                assert isinstance(value_id, int)
                self.collection_to_model_ids_to_delete[field_data["to_collection"]].add(
                    value_id
                )
                self.fqids_to_delete.add(f"{field_data['to_collection']}/{value_id}")
            case _:
                if not self.exists(target_fqid):
                    return
                if is_list_field(field_data["to_field"]):
                    self.fqid_to_list_removal[target_fqid][
                        field_data["to_field"]
                    ].append(base_id)
                else:
                    self.fqid_to_empty_fields[target_fqid].add(field_data["to_field"])

    # code below here is almost an exact copy from the countdown code
    # of the speaker delete code structure.
    def calculate_speakers_to_delete(
        self, musers_to_delete: dict[int, dict[str, Any]]
    ) -> tuple[list[int], list[BaseRequestEvent]]:
        """
        Returns the list of speaker_ids that should be deleted ad pos 0
        and the list of events for the countdown changes for that deletion at pos 1
        """
        speaker_ids = [
            speaker_id
            for muser in musers_to_delete.values()
            for speaker_id in (muser.get("speaker_ids") or [])
        ]
        speakers = self.reader.get_many(
            [
                GetManyRequestPart(
                    "speaker",
                    speaker_ids,
                    [
                        "meeting_id",
                        "list_of_speakers_id",
                        "structure_level_list_of_speakers_id",
                        "speech_state",
                        "begin_time",
                        "end_time",
                        "pause_time",
                        "point_of_order",
                        "unpause_time",
                        "id",
                    ],
                )
            ]
        ).get("speaker", {})
        delete_speaker_ids = [
            id_
            for id_, speaker in speakers.items()
            if speaker.get("begin_time") is None
        ]
        self.countdown_change_events: list[BaseRequestEvent] = []
        # for speaker_id in delete_speaker_ids:
        #     speaker = speakers[speaker_id]
        #     if (
        #         speaker.get("begin_time")
        #         and not speaker.get("end_time")
        #         and not speaker.get("pause_time")
        #     ):
        #         self.decrease_structure_level_countdown(self.end_time, speaker)
        #     if speaker.get("begin_time") and not speaker.get("end_time"):
        #         self.reset_los_countdown(speaker["meeting_id"])
        return delete_speaker_ids, self.countdown_change_events

    # def decrease_structure_level_countdown(
    #     self, now: int, speaker: dict[str, Any]
    # ) -> None:
    #     if (
    #         (level_id := speaker.get("structure_level_list_of_speakers_id"))
    #         and (
    #             speaker.get("speech_state")
    #             not in (
    #                 "interposed_question",
    #                 "intervention",
    #             )
    #         )
    #         and not speaker.get("point_of_order")
    #     ):
    #         # only update the level if the speaker was not paused and the speech state demands it
    #         start_time = cast(int, speaker.get("unpause_time", speaker["begin_time"]))
    #         fqid = fqid_from_collection_and_id(
    #             "structure_level_list_of_speakers", level_id
    #         )
    #         db_instance = self.reader.get(
    #             fqid,
    #             ["remaining_time"],
    #         )
    #         self.countdown_change_events.append(
    #             RequestUpdateEvent(
    #                 fqid,
    #                 fields={
    #                     "current_start_time": None,
    #                     "remaining_time": db_instance["remaining_time"]
    #                     - (now - start_time),
    #                 },
    #             )
    #         )

    # def reset_los_countdown(
    #     self,
    #     meeting_id: int,
    # ) -> None:
    #     meeting = self.reader.get(
    #         fqid_from_collection_and_id("meeting", meeting_id),
    #         ["list_of_speakers_couple_countdown", "list_of_speakers_countdown_id"],
    #     )
    #     if meeting.get("list_of_speakers_couple_countdown") and meeting.get(
    #         "list_of_speakers_countdown_id"
    #     ):
    #         self.reset_countdown(meeting["list_of_speakers_countdown_id"])

    # def reset_countdown(
    #     self,
    #     countdown_id: int,
    # ) -> None:
    #     countdown = self.reader.get(
    #         fqid_from_collection_and_id("projector_countdown", countdown_id),
    #         ["countdown_time", "default_time"],
    #     )
    #     running = False
    #     countdown_time = countdown["default_time"]

    #     self.countdown_change_events.append(
    #         RequestUpdateEvent(
    #             fqid_from_collection_and_id("projector_countdown", countdown_id),
    #             fields={
    #                 "running": running,
    #                 "countdown_time": countdown_time,
    #             },
    #         )
    #     )
