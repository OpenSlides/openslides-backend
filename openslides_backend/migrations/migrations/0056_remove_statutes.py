from collections import defaultdict
from typing import Any

from datastore.migrations import BaseModelMigration
from datastore.reader.core.requests import GetManyRequestPart
from datastore.shared.util import (
    collection_and_id_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from datastore.writer.core import (
    BaseRequestEvent,
    RequestDeleteEvent,
    RequestUpdateEvent,
)


class Migration(BaseModelMigration):
    """
    This migration removes all relations to and the statute motions/paragraphs themselves. This requieres to also delete all dangling models.
    Poll candidate lists and their candidates of deleted polls will not be deleted since they are not expected in this context.
    """

    target_migration_index = 57

    simple_fields = [
        "motion_ids",
        "forwarded_motion_ids",
        "list_of_speakers_ids",
        "speaker_ids",
        "poll_ids",
        # "option_ids",
        # "vote_ids",
    ]
    motion_reference_id_list_update = [
        {
            "field": "state_id",
            "collection": "motion_state",
            "foreign_field": "motion_ids",
        },
        {
            "field": "recommendation_id",
            "collection": "motion_state",
            "foreign_field": "motion_recommendation_ids",
        },
        {
            "field": "state_extension_reference_ids",
            "collection": "motion",
            "foreign_field": "referenced_in_motion_state_extension_ids",
        },
        {
            "field": "referenced_in_motion_state_extension_ids",
            "collection": "motion",
            "foreign_field": "state_extension_reference_ids",
        },
        {
            "field": "recommendation_extension_reference_ids",
            "collection": "motion",
            "foreign_field": "referenced_in_motion_recommendation_extension_ids",
        },
        {
            "field": "referenced_in_motion_recommendation_extension_ids",
            "collection": "motion",
            "foreign_field": "recommendation_extension_reference_ids",
        },
        {
            "field": "category_id",
            "collection": "motion_category",
            "foreign_field": "motion_ids",
        },
        {
            "field": "block_id",
            "collection": "motion_block",
            "foreign_field": "motion_ids",
        },
        {
            "field": "supporter_meeting_user_ids",
            "collection": "meeting_user",
            "foreign_field": "supported_motion_ids",
        },
        {
            "field": "attachment_ids",
            "collection": "mediafile",
            "foreign_field": "attachment_ids",
        },
        {
            "field": "meeting_id",
            "collection": "meeting",
            "foreign_field": "motion_ids",
        },
    ]
    motion_reference_id_list_delete = [
        {
            "field": "submitter_ids",
            "collection": "motion_submitter",
            "meeting_field": "motion_submitter_ids",
            "meeting_user_field": "motion_submitter_ids",
        },
        {
            "field": "editor_ids",
            "collection": "motion_editor",
            "meeting_field": "motion_editor_ids",
            "meeting_user_field": "motion_editor_ids",
        },
        {
            "field": "working_group_speaker_ids",
            "collection": "motion_working_group_speaker",
            "meeting_field": "motion_working_group_speaker_ids",
            "meeting_user_field": "motion_working_group_speaker_ids",
        },
        {
            "field": "change_recommendation_ids",
            "collection": "motion_change_recommendation",
            "meeting_field": "motion_change_recommendation_ids",
        },
        {
            "field": "comment_ids",
            "collection": "motion_comment",
            "meeting_field": "motion_comment_ids",
        },
        {
            "field": "personal_note_ids",
            "collection": "personal_note",
            "meeting_field": "personal_note_ids",
            "meeting_user_field": "personal_note_ids",
        },
    ]

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        to_remove_in_meetings: defaultdict[int, defaultdict[str, list]] = defaultdict(
            lambda: defaultdict(list)
        )
        to_remove_in_projectors: defaultdict[int, defaultdict[str, list]] = defaultdict(
            lambda: defaultdict(list)
        )
        to_remove_in_users: defaultdict[int, defaultdict[str, list]] = defaultdict(
            lambda: defaultdict(list)
        )
        tags_to_update: defaultdict[int, set[str]] = defaultdict(set)
        meeting_users_to_update: defaultdict[str, defaultdict[str, list]] = defaultdict(
            lambda: defaultdict(list)
        )

        # delete all statute paragraphs
        statute_paragraphs = self.reader.get_all(
            "motion_statute_paragraph", ["meeting_id"]
        )
        for statute_paragraph_id, statute_paragraph in statute_paragraphs.items():
            events.append(
                RequestDeleteEvent(
                    fqid_from_collection_and_id(
                        "motion_statute_paragraph", statute_paragraph_id
                    )
                )
            )
            to_remove_in_meetings[statute_paragraph.get("meeting_id", 0)][
                "statute_paragraph_ids"
            ].append(statute_paragraph_id)

        self.delete_motions_update_related(
            to_remove_in_meetings,
            meeting_users_to_update,
            tags_to_update,
            to_remove_in_projectors,
            to_remove_in_users,
            events,
        )

        for projector_id, projector in to_remove_in_projectors.items():
            for state in ["current", "preview", "history"]:
                if (projection_ids := projector[f"{state}_projection_ids"]) and (
                    response := self.update_relations(
                        fqid_from_collection_and_id("projector", projector_id),
                        f"{state}_projection_ids",
                        set(projection_ids),
                    )
                ):
                    events.append(response)

        for user_id, user_data in to_remove_in_users.items():
            user_fqid = fqid_from_collection_and_id("user", user_id)
            user = self.reader.get(user_fqid)
            events.append(
                RequestUpdateEvent(
                    user_fqid,
                    {
                        field_name: self.subtract_ids(
                            user.get(field_name), ids_to_delete
                        )
                        for field_name, ids_to_delete in user_data.items()
                    },
                )
            )

        for meeting_user_fqid, meeting_user_data in meeting_users_to_update.items():
            meeting_user = self.reader.get(meeting_user_fqid)
            events.append(
                RequestUpdateEvent(
                    meeting_user_fqid,
                    {
                        field_name: self.subtract_ids(
                            meeting_user.get(field_name), ids_to_delete
                        )
                        for field_name, ids_to_delete in meeting_user_data.items()
                    },
                )
            )

        for tag_id, object_fqids in tags_to_update.items():
            if response := self.update_relations(
                fqid_from_collection_and_id("tag", tag_id),
                "tagged_ids",
                object_fqids,
                "agenda_item",
            ):
                events.append(response)

        # find and update statute related motion workflows. That will make sure to get all.
        motion_workflows = self.reader.get_all(
            "motion_workflow", ["default_statute_amendment_workflow_meeting_id"]
        )
        for workflow_id, workflow in motion_workflows.items():
            if workflow.get("default_statute_amendment_workflow_meeting_id", ""):
                events.append(
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("motion_workflow", workflow_id),
                        {"default_statute_amendment_workflow_meeting_id": None},
                    )
                )

        # update meetings
        meetings = self.reader.get_all(
            "meeting",
            [
                *[
                    meeting_field.get("meeting_field", "")
                    for meeting_field in self.motion_reference_id_list_delete
                ],
                "structure_level_list_of_speakers_ids",
                "agenda_item_ids",
                "all_projection_ids",
                *self.simple_fields,
            ],
        )
        for meeting_id, meeting in meetings.items():
            meeting_fqid = fqid_from_collection_and_id("meeting", meeting_id)

            # update generic approach fields
            additional_meeting_update_fields = {}
            for entry in self.motion_reference_id_list_delete:
                foreign_field = entry.get("meeting_field", "")
                deleted_ids = to_remove_in_meetings[meeting_id][
                    entry.get("collection", "")
                ]
                model_ids = meeting.get(foreign_field)
                model_ids = self.subtract_ids(model_ids, deleted_ids)
                additional_meeting_update_fields[foreign_field] = model_ids

            # update manual approach fields
            meeting_update_data: dict[str, Any] = {
                meeting_field: self.subtract_ids(
                    meeting.get(meeting_field),
                    to_remove_in_meetings[meeting_id].get(field),
                )
                for meeting_field, field in {
                    "structure_level_list_of_speakers_ids": "structure_level_los_ids",
                    "all_projection_ids": "projection_ids",
                    **{d_field: d_field for d_field in self.simple_fields},
                }.items()
            }
            if agenda_item_ids := to_remove_in_meetings[meeting_id].get(
                "agenda_item_ids"
            ):
                for agenda_item_id in agenda_item_ids:
                    events.append(
                        RequestDeleteEvent(
                            fqid_from_collection_and_id("agenda_item", agenda_item_id)
                        )
                    )
            agenda_item_ids = self.subtract_ids(
                meeting.get("agenda_item_ids"),
                agenda_item_ids,
            )

            events.append(
                RequestUpdateEvent(
                    meeting_fqid,
                    {
                        **meeting_update_data,
                        **additional_meeting_update_fields,
                        "motions_statutes_enabled": None,
                        "motions_statute_recommendations_by": None,
                        "motion_statute_paragraph_ids": None,
                        "motions_default_statute_amendment_workflow_id": None,
                        "agenda_item_ids": agenda_item_ids,
                    },
                )
            )

        # update lost references in bulk TODO delete when finished
        for collection, update_schema_part in self.update_schema.items():
            self.generic_update(
                events,
                collection,
                update_schema_part,
                self.to_be_updated[collection],
                self.deleted_instances,
            )
        return events

    def delete_motions_update_related(
        self,
        to_remove_in_meetings: defaultdict[int, defaultdict[str, list]],
        meeting_users_to_update: defaultdict[str, defaultdict[str, list]],
        tags_to_update: defaultdict[int, set[str]],
        to_remove_in_projectors: defaultdict[int, defaultdict[str, list]],
        to_remove_in_users: defaultdict[int, defaultdict[str, list]],
        events: list[BaseRequestEvent],
    ) -> None:
        # find statute related motions
        motions = self.reader.get_all("motion", ["statute_paragraph_id", "meeting_id"])
        for motion_id, motion in motions.items():
            if motion.get("statute_paragraph_id", ""):
                to_remove_in_meetings[motion.get("meeting_id", 0)]["motion_ids"].append(
                    motion_id
                )
        
        for meeting_id, to_remove_dict in to_remove_in_meetings.items():
            # Wie ist das mit den forwarded motions? Sind motions anderer Meetings relevant?
            deleted_motions_ids = to_remove_dict.get("motion_ids", [])
            for motion_id in deleted_motions_ids:
                motion_fqid = fqid_from_collection_and_id("motion", motion_id)
                motion = self.reader.get(motion_fqid)
                meeting_id = motion.get("meeting_id", "")

                self.list_update(motion, set(deleted_motions_ids), events)
                self.list_delete(
                    motion,
                    to_remove_in_meetings,
                    meeting_users_to_update,
                    meeting_id,
                    events,
                )

        deletion_schema: dict[str, dict[str, list[str]]] = {
            "meeting": {
                "precursors": [],
                "update_collections": [],
                "update_foreign_fields": [],
            },
            "group": {
                "precursors": [],
                "update_collections": [],
                "update_foreign_fields": [],
            },
            "projector": {
                "precursors": [],
                "update_collections": [],
                "update_foreign_fields": [],
            },
            "tag": {
                "precursors": [],
                "update_collections": [],
                "update_foreign_fields": [],
            },
            "meeting_user": {
                "precursors": [],
                "update_collections": [],
                "update_foreign_fields": [],
            },
            "point_of_order_category": {
                "precursors": [],
                "update_collections": [],
                "update_foreign_fields": [],
            },
            "motion": {
                "precursors": [],
                "cascaded_delete_collections": [
                    "poll",
                    "projection",
                    "agenda_item",
                    "list_of_speakers",
                ],
                "cascaded_delete_fields": [
                    "poll_ids",
                    "projection_ids",
                    "agenda_item_id",
                    "list_of_speakers_id",
                ],
                "update_ids_fields": ["meeting_id", "tag_ids"],
                "update_collections": ["meeting", "tag"],
                "update_foreign_fields": ["motion_ids", "generic_tagged_ids"],
            },
            "poll": {
                "precursors": ["motion"],
                "cascaded_delete_collections": ["option", "projection"],
                "cascaded_delete_fields": ["option_ids", "projection_ids"],
                "update_ids_fields": ["meeting_id", "entitled_group_ids", "voted_ids"],
                "update_collections": ["meeting", "group", "user"],
                "update_foreign_fields": ["poll_ids", "poll_ids", "poll_voted_ids"],
            },
            "option": {
                "precursors": ["poll"],
                "cascaded_delete_collections": ["vote"],
                "cascaded_delete_fields": ["vote_ids"],
                "update_ids_fields": [
                    "meeting_id",
                    "content_object_id",
                    "content_object_id",
                    "content_object_id",
                ],
                "update_collections": [
                    "meeting",
                    "motion",
                    "poll_candidate_list",
                    "user",
                ],
                "update_foreign_fields": [
                    "option_ids",
                    "option_ids",
                    "option_id",
                    "option_ids",
                ],
            },
            "vote": {
                "precursors": ["option"],
                "cascaded_delete_collections": [],
                "cascaded_delete_fields": [],
                "update_ids_fields": ["meeting_id", "user_id", "delegated_user_id"],
                "update_collections": ["meeting", "user", "user"],
                "update_foreign_fields": ["vote_ids", "vote_ids", "delegated_vote_ids"],
            },
            "agenda_item": {
                "precursors": ["motion"],
                "cascaded_delete_collections": ["projection"],
                "cascaded_delete_fields": ["projection_ids"],
                "update_ids_fields": [
                    "meeting_id",
                    "child_ids",
                    "parent_id",
                    "tag_ids",
                ],
                "update_collections": ["meeting", "agenda_item", "agenda_item", "tag"],
                "update_foreign_fields": [
                    "agenda_item_ids",
                    "parent_id",
                    "child_ids",
                    "generic_tagged_ids",
                ],
            },
            "list_of_speakers": {
                "precursors": ["motion"],
                "cascaded_delete_collections": [
                    "projection",
                    "speaker",
                    "structure_level_list_of_speakers",
                ],
                "cascaded_delete_fields": [
                    "projection_ids",
                    "speaker_ids",
                    "structure_level_list_of_speakers_ids",
                ],
                "update_ids_fields": ["meeting_id"],
                "update_collections": ["meeting"],
                "update_foreign_fields": ["list_of_speakers_ids"],
            },
            "speaker": {
                "precursors": ["list_of_speakers"],
                "cascaded_delete_collections": [],
                "cascaded_delete_fields": [],
                "update_ids_fields": [
                    "meeting_id",
                    "meeting_user_id",
                    "point_of_order_category_id",
                ],
                "update_collections": [
                    "meeting",
                    "meeting_user",
                    "point_of_order_category",
                ],
                "update_foreign_fields": ["speaker_ids", "speaker_ids", "speaker_ids"],
            },
            "structure_level_list_of_speakers": {
                "precursors": ["list_of_speakers"],
                "cascaded_delete_collections": [],
                "cascaded_delete_fields": [],
                "update_ids_fields": [
                    "meeting_id",
                    "meeting_user_ids",
                    "structure_level_id",
                ],
                "update_collections": ["meeting", "meeting_user", "structure_level"],
                "update_foreign_fields": [
                    "structure_level_list_of_speakers_ids",
                    "structure_level_list_of_speakers_ids",
                    "structure_level_list_of_speakers_ids",
                ],
            },
            "structure_level": {
                "precursors": ["list_of_speakers"],
                "cascaded_delete_collections": [],
                "cascaded_delete_fields": [],
                "update_ids_fields": ["meeting_id", "meeting_user_ids"],
                "update_collections": ["meeting", "meeting_user"],
                "update_foreign_fields": [
                    "structure_level_list_of_speakers_ids",
                    "structure_level_list_of_speakers_ids",
                ],
            },
            "projection": {
                "precursors": ["motion", "poll", "agenda_item", "list_of_speakers"],
                "cascaded_delete_collections": [],
                "cascaded_delete_fields": [],
                "update_ids_fields": [
                    "meeting_id",
                    "current_projector_id",
                    "preview_projector_id",
                    "history_projector_id",
                ],
                "update_collections": [
                    "meeting",
                    "projector",
                    "projector",
                    "projector",
                ],
                "update_foreign_fields": [
                    "all_projection_ids",
                    "current_projection_ids",
                    "preview_projection_ids",
                    "history_projection_ids",
                ],
            },
        }
        self.deleted_instances: dict[str, set | None] = {
            collection: None for collection in deletion_schema.keys()
        }
        self.update_schema: defaultdict[str, list[str]] = defaultdict(list)
        for schema_part in deletion_schema.values():
            for collection, collection_fields in zip(
                schema_part["update_collections"], schema_part["update_foreign_fields"]
            ):
                if "generic_" in collection_fields:
                    collection_fields = collection_fields.lstrip("generic_")
                self.update_schema[collection].extend([collection_fields])
        to_be_deleted: dict[str, set] = {
            collection: set() for collection in deletion_schema.keys()
        }
        # dicts structure is {collection : id : fields : values}
        self.to_be_updated: dict[str, dict[int, dict[str, list]]] = {
            collection: defaultdict(lambda: defaultdict(list))
            for collection in self.update_schema.keys()
        }
        # set deletion root TODO use the scheme from above
        to_be_deleted["motion"] = {
            motion_id 
            for to_remove_dict in to_remove_in_meetings.values()
            for motion_id in to_remove_dict.get("motion_ids", [])
        }
        for meeting_id, to_remove_dict in to_remove_in_meetings.items():
            # Wie ist das mit den forwarded motions? Sind motions anderer Meetings relevant?
            deleted_motions_ids = to_remove_dict.get("motion_ids", [])

        # delete until all have at least empty list (means finished)
        while not self.is_finished(self.deleted_instances):
            for collection, schema_part in deletion_schema.items():
                # check collection wasn't handled yet
                if self.deleted_instances[collection] is None:
                    # check precursors have finished
                    if not any(
                        precursor
                        for precursor in schema_part["precursors"]
                        if self.deleted_instances[precursor] is None
                    ):
                        self.generic_delete(
                            events,
                            collection,
                            schema_part,
                            to_be_deleted,
                            self.to_be_updated,
                        )
                        # safe all ids in deleted
                        self.deleted_instances[collection] = to_be_deleted[collection]

    def list_update(self, motion: dict, deleted_motions_ids: set, events: list) -> None:
        """updates models related with motion that won't get deleted."""
        for entry in self.motion_reference_id_list_update:
            field_name = entry.get("field", "")
            foreign_field = entry.get("foreign_field", "")
            collection_name = entry.get("collection", "")
            if field_value := motion.get(field_name):
                if isinstance(field_value, list):
                    for model_id in field_value:
                        if isinstance(model_id, str):
                            fqid = model_id
                            collection_name = model_id.split("/")[0]
                            model_id = int(model_id.split("/")[1])
                        else:
                            fqid = fqid_from_collection_and_id(
                                collection_name, model_id
                            )
                        if (
                            collection_name == "motion"
                            and model_id in deleted_motions_ids
                        ):
                            continue
                        if response := self.update_relations(
                            fqid,
                            foreign_field,
                            deleted_motions_ids,
                            "motion",
                        ):
                            events.append(response)
                else:
                    fqid = fqid_from_collection_and_id(collection_name, field_value)
                    if response := self.update_relations(
                        fqid, foreign_field, deleted_motions_ids
                    ):
                        events.append(response)

    def list_delete(
        self,
        motion: dict,
        to_remove_in_meetings: defaultdict[int, defaultdict[str, list]],
        meeting_users_to_update: defaultdict[str, defaultdict[str, list]],
        meeting_id: int,
        events: list,
    ) -> None:
        """deletes not cascading models related with motion"""
        for entry in self.motion_reference_id_list_delete:
            field_name = entry.get("field", "")
            collection_name = entry.get("collection", "")
            if field_value := motion.get(field_name):
                for model_id in field_value:
                    events.append(
                        RequestDeleteEvent(
                            fqid_from_collection_and_id(collection_name, model_id)
                        )
                    )
                    to_remove_in_meetings[meeting_id][collection_name].append(model_id)
                    # do some manual updates one layer down
                    model = self.reader.get(
                        fqid_from_collection_and_id(collection_name, model_id)
                    )
                    if collection_name == "motion_comment":
                        comment_section_fqid = fqid_from_collection_and_id(
                            "motion_comment_section",
                            model.get("section_id", 0),
                        )
                        if response := self.update_relations(
                            comment_section_fqid, "comment_ids", model_id
                        ):
                            events.append(response)

                    if meeting_user_field := entry.get("meeting_user_field"):
                        meeting_user_fqid = fqid_from_collection_and_id(
                            "meeting_user", model.get("meeting_user_id", 0)
                        )
                        meeting_users_to_update[meeting_user_fqid][
                            meeting_user_field
                        ].append(model_id)

    def is_finished(self, deleted_instances: dict) -> bool:
        for collection in deleted_instances.values():
            if collection is None:
                return False
        return True

    def generic_delete(
        self,
        events: list,
        collection: str,
        collection_delete_schema: dict[str, list],
        to_be_deleted: dict,
        to_be_updated: dict,
    ) -> None:
        to_be_deleted_ids = to_be_deleted[collection]
        # get models to be deleted now
        models = self.reader.get_many(
            [
                GetManyRequestPart(
                    collection,
                    to_be_deleted_ids,
                    collection_delete_schema.get("cascaded_delete_fields", [])
                    + collection_delete_schema.get("update_ids_fields", []),
                )
            ]
        ).get(collection, {})
        for model_id, model in models.items():
            # stage related collection instances for later deletion
            for foreign_collection, own_field in zip(
                collection_delete_schema["cascaded_delete_collections"],
                collection_delete_schema["cascaded_delete_fields"],
            ):
                if foreign_id_or_ids := model.get(own_field):
                    if isinstance(foreign_id_or_ids, list) and isinstance(
                        foreign_id_or_ids[0], str
                    ):
                        foreign_id_or_ids = [
                            id_from_fqid(foreign_id) for foreign_id in foreign_id_or_ids
                        ]
                    elif isinstance(foreign_id_or_ids, str):
                        foreign_id_or_ids = [id_from_fqid(foreign_id_or_ids)]
                    elif isinstance(foreign_id_or_ids, int):
                        foreign_id_or_ids = [foreign_id_or_ids]
                    to_be_deleted[foreign_collection].update(foreign_id_or_ids)
            # stage instance ids for update in related collection instances
            for foreign_collection, foreign_ids_field, foreign_field in zip(
                collection_delete_schema["update_collections"],
                collection_delete_schema["update_ids_fields"],
                collection_delete_schema["update_foreign_fields"],
            ):
                # TODO delete
                if foreign_collection == "tag":
                    pass

                def storage_helper(
                    foreign_ids: list[int | str],
                    foreign_collection: str,
                    foreign_field: str,
                    model_id: int,
                    to_be_updated: dict,
                ) -> None:
                    for foreign_id in foreign_ids:
                        if isinstance(foreign_id, str):
                            tmp_foreign_collection, foreign_id = (
                                collection_and_id_from_fqid(foreign_id)
                            )
                            # generic fields have different collections in themselves
                            if tmp_foreign_collection != foreign_collection:
                                return
                        # need to store own collection context for generic foreign field
                        if "generic_" in foreign_field:
                            foreign_field = foreign_field.lstrip("generic_")
                            model_id = fqid_from_collection_and_id(collection, model_id)
                        to_be_updated[foreign_collection][foreign_id][
                            foreign_field
                        ].append(model_id)

                if foreign_ids_field in model:
                    if "_ids" in foreign_ids_field:
                        foreign_ids = model[foreign_ids_field]
                    else:
                        foreign_ids = [model[foreign_ids_field]]
                    storage_helper(
                        foreign_ids,
                        foreign_collection,
                        foreign_field,
                        model_id,
                        to_be_updated,
                    )
        # finally delete
        for to_be_deleted_id in to_be_deleted_ids:
            events.append(
                RequestDeleteEvent(
                    fqid_from_collection_and_id(collection, to_be_deleted_id)
                )
            )

    def generic_update(
        self,
        events: list,
        collection: str,
        schema: list[str],
        to_be_updated_in_collection: dict,
        deleted_instances: dict,
    ) -> None:
        to_remove = []
        # if there were no instances deleted we don't need to remove them from our update list.
        if collection in deleted_instances:
            for instance_id in to_be_updated_in_collection.keys():
                if instance_id in deleted_instances[collection]:
                    to_remove.append(instance_id)
            for instance_id in to_remove:
                del to_be_updated_in_collection[instance_id]

        instances = self.reader.get_many(
            [
                GetManyRequestPart(
                    collection,
                    [instance_id for instance_id in to_be_updated_in_collection.keys()],
                    schema,
                )
            ]
        ).get(collection, {})
        for instance_id, fields_and_ids in to_be_updated_in_collection.items():
            instance = instances.get(instance_id, {})
            # TODO delete
            if collection == "tag":
                pass
            # save the instances data without the deleted ids
            for field, without_ids in fields_and_ids.items():
                if "_ids" in field:
                    db_ids = instance.get(field, [])
                else:
                    db_ids = [instance.get(field, [])]
                fields_and_ids[field] = self.subtract_ids(db_ids, without_ids)
            events.append(
                RequestUpdateEvent(
                    fqid_from_collection_and_id(collection, instance_id), fields_and_ids
                )
            )
            pass  # TODO delete

    def update_relations(
        self,
        fqid: str,
        foreign_field: str,
        deleted_ids: int | set[int] | set[str],
        origin_collection: str | None = None,
    ) -> RequestUpdateEvent | None:
        """
        This updates the relations in the by `fqid` given object in the `foreign_field` by subtracting the `deleted_ids`.
        The deleted ids can either be a singular id or a set of either fqids or ids.
        The `origin_collection` is needed if the foreign field is generic.
        """
        model = self.reader.get(fqid, [foreign_field])
        if field_value := model.get(foreign_field, []):
            if isinstance(deleted_ids, set):
                # if target field is generic and deleted_ids contains ints, convert to fqids
                if isinstance(field_value[0], str) and isinstance(
                    next(iter(deleted_ids)), int
                ):
                    assert origin_collection is not None
                    tmp_ids = set()
                    for deleted_id in deleted_ids:
                        tmp_ids.add(f"{origin_collection}/{deleted_id}")
                    deleted_ids = tmp_ids
                field_value = list(set(field_value) - deleted_ids)
            # deleted_ids is an int and so is field_value
            elif field_value == deleted_ids:
                field_value = None
            # field_value is int deleted_ids is set
            else:
                field_value.remove(deleted_ids)
            if field_value == []:
                field_value = None
            return RequestUpdateEvent(fqid, {foreign_field: field_value})
        return None

    def subtract_ids(
        self, front_ids: list | None, without_ids: list | None
    ) -> list | None:
        """
        this subtracts items of a list from another list in an efficient manner
        returns a list
        """
        if not front_ids:
            return None
        if not without_ids:
            return front_ids
        return list(set(front_ids) - set(without_ids)) or None
