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

    # Wie ist das mit den forwarded motions? Sind motions anderer Meetings relevant?
    # TODO lead_motion_id, amendment_ids, sort_parent_id, sort_child_ids, origin_id,
    # origin_meeting_id, derived_motion_ids, all_origin_ids, all_derived_motion_ids,
    # identical_motion_ids
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
        "motion_state": {
            "precursors": [],
            "update_collections": [],
            "update_foreign_fields": [],
        },
        "motion_category": {
            "precursors": [],
            "update_collections": [],
            "update_foreign_fields": [],
        },
        "motion_block": {
            "precursors": [],
            "update_collections": [],
            "update_foreign_fields": [],
        },
        "meeting_mediafile": {
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
                "motion_submitter",
                "motion_editor",
                "motion_working_group_speaker",
                "personal_note",
                "motion_comment",
                "motion_change_recommendation",
            ],
            "cascaded_delete_fields": [
                "poll_ids",
                "projection_ids",
                "agenda_item_id",
                "list_of_speakers_id",
                "submitter_ids",
                "editor_ids",
                "working_group_speaker_ids",
                "personal_note_ids",
                "comment_ids",
                "change_recommendation_ids",
            ],
            "update_ids_fields": [
                "meeting_id",
                "tag_ids",
                "state_id",
                "recommendation_id",
                "state_extension_reference_ids",
                "referenced_in_motion_state_extension_ids",
                "recommendation_extension_reference_ids",
                "referenced_in_motion_recommendation_extension_ids",
                "category_id",
                "block_id",
                "supporter_meeting_user_ids",
                "attachment_meeting_mediafile_ids",
            ],
            "update_collections": [
                "meeting",
                "tag",
                "motion_state",
                "motion_state",
                "motion",
                "motion",
                "motion",
                "motion",
                "motion_category",
                "motion_block",
                "meeting_user",
                "meeting_mediafile",
            ],
            "update_foreign_fields": [
                "motion_ids",
                "generic_tagged_ids",
                "motion_ids",
                "motion_recommendation_ids",
                "referenced_in_motion_state_extension_ids",
                "state_extension_reference_ids",
                "referenced_in_motion_recommendation_extension_ids",
                "recommendation_extension_reference_ids",
                "motion_ids",
                "motion_ids",
                "supported_motion_ids",
                "generic_attachment_ids",
            ],
        },
        "motion_submitter": {
            "precursors": ["motion"],
            "cascaded_delete_collections": [],
            "cascaded_delete_fields": [],
            "update_ids_fields": ["meeting_id", "meeting_user_id"],
            "update_collections": ["meeting", "meeting_user"],
            "update_foreign_fields": [
                "motion_submitter_ids",
                "motion_submitter_ids",
            ],
        },
        "motion_editor": {
            "precursors": ["motion"],
            "cascaded_delete_collections": [],
            "cascaded_delete_fields": [],
            "update_ids_fields": ["meeting_id", "meeting_user_id"],
            "update_collections": ["meeting", "meeting_user"],
            "update_foreign_fields": [
                "motion_editor_ids",
                "motion_editor_ids",
            ],
        },
        "motion_working_group_speaker": {
            "precursors": ["motion"],
            "cascaded_delete_collections": [],
            "cascaded_delete_fields": [],
            "update_ids_fields": ["meeting_id", "meeting_user_id"],
            "update_collections": ["meeting", "meeting_user"],
            "update_foreign_fields": [
                "motion_working_group_speaker_ids",
                "motion_working_group_speaker_ids",
            ],
        },
        "personal_note": {
            "precursors": ["motion"],
            "cascaded_delete_collections": [],
            "cascaded_delete_fields": [],
            "update_ids_fields": ["meeting_id", "meeting_user_id"],
            "update_collections": ["meeting", "meeting_user"],
            "update_foreign_fields": [
                "personal_note_ids",
                "personal_note_ids",
            ],
        },
        "motion_comment": {
            "precursors": ["motion"],
            "cascaded_delete_collections": [],
            "cascaded_delete_fields": [],
            "update_ids_fields": ["meeting_id", "section_id"],
            "update_collections": ["meeting", "motion_comment_section"],
            "update_foreign_fields": ["motion_comment_ids", "comment_ids"],
        },
        "motion_comment_section": {
            "precursors": ["motion_comment"],
            "cascaded_delete_collections": [],
            "cascaded_delete_fields": [],
            "update_ids_fields": ["meeting_id"],
            "update_collections": ["meeting"],
            "update_foreign_fields": [
                "motion_comment_section_ids",
            ],
        },
        "motion_change_recommendation": {
            "precursors": ["motion"],
            "cascaded_delete_collections": [],
            "cascaded_delete_fields": [],
            "update_ids_fields": ["meeting_id"],
            "update_collections": ["meeting"],
            "update_foreign_fields": [
                "motion_change_recommendation_ids",
            ],
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

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        """migrates all models by deleting everything related to statutes and updating the relations."""
        events: list[BaseRequestEvent] = []

        # delete all statute paragraphs TODO subprocess of motion delete?
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
            [],
        )
        for meeting_id, meeting in meetings.items():
            meeting_fqid = fqid_from_collection_and_id("meeting", meeting_id)
            events.append(
                RequestUpdateEvent(
                    meeting_fqid,
                    {
                        "motions_statutes_enabled": None,
                        "motions_statute_recommendations_by": None,
                        "motion_statute_paragraph_ids": None,
                        "motions_default_statute_amendment_workflow_id": None,
                    },
                )
            )

        # delete motions cascadingly and update related
        motions = self.reader.get_all("motion", ["statute_paragraph_id", "meeting_id"])
        self.delete_update_by_schema(
            {
                "motion": {
                    motion_id
                    for motion_id, motion in motions.items()
                    if motion.get("statute_paragraph_id")
                }
            },
            self.deletion_schema,
            events,
        )
        return events

    def delete_update_by_schema(
        self,
        initial_deletes: dict[str, set],
        deletion_schema:dict[str, dict[str, list[str]]],
        events: list[BaseRequestEvent],
    ) -> None:
        """
        This deletes all models specified by a deletion schema of the shape:
        {
            super collection: str
                {
                    "precursors":
                        collections: list[str]
                    "cascaded_delete_collections":
                        collections: list[str]
                    "cascaded_delete_fields":
                        super collections fields of delete collection ids: list[str]
                    "update_ids_fields":
                        super collections fields of update collection ids: list[str]
                    "update_collections":
                        collections to be updated: list[str],
                    "update_foreign_fields":
                        fields of update collections to be updated by removing the super collections id: list[str],
                },
            ...
        }
        The order delete or update info are given, needs to be matching since these are matched by zip(). This may require to state
        a collection for deletion or update multiple times if there are multiple fields relating from one collection to the other.
        This function auto magically handles 1:1, 1:n, n:m relations. It can also handle generic relations.
        If the update_foreign_field is of generic type the field name needs to be supplemented with a leading "generic_".
        It first deletes all models denoted by initial_deletes and then marks more models for deletion and update.
        Iteratively checks to handle deletion for the models marked for deletion by all collections of cascaded_delete_collections.
        A collections models are only deleted if all precursors have finished.
        After all deletions are completed the relations of all deleted models are updated in their related models.
        Collections that are not deleted but being updated need to be specified like the others but it is sufficient to just give
        empty lists of precursors, update_collections and update_foreign_fields.
        Returns the list of delete and update requests.
        """

        update_schema: defaultdict[str, list[str]] = defaultdict(list)
        for schema_part in deletion_schema.values():
            for collection, collection_fields in zip(
                schema_part["update_collections"], schema_part["update_foreign_fields"]
            ):
                if "generic_" in collection_fields:
                    collection_fields = collection_fields.lstrip("generic_")
                update_schema[collection].extend([collection_fields])
        # dicts structure is {collection : id : fields : values}
        to_be_updated: dict[str, dict[int, dict[str, list[str | int]]]] = {
            collection: defaultdict(lambda: defaultdict(list[str | int]))
            for collection in update_schema.keys()
        }
        to_be_deleted: dict[str, set] = {
            collection: set() for collection in deletion_schema.keys()
        }
        deleted_instances: dict[str, set | None] = {
            collection: None for collection in deletion_schema.keys()
        }
        # set deletion root by finding statute related motions
        for collection, to_delete_ids in initial_deletes.items():
            to_be_deleted[collection] = to_delete_ids
        # delete until all have at least an empty list (means finished)
        while not self.is_finished(deleted_instances):
            for collection, schema_part in deletion_schema.items():
                # check collection wasn't handled yet
                if deleted_instances[collection] is None:
                    # check precursors have finished
                    if not any(
                        precursor
                        for precursor in schema_part["precursors"]
                        if deleted_instances[precursor] is None
                    ):
                        self.generic_delete(
                            events,
                            collection,
                            schema_part,
                            to_be_deleted,
                            to_be_updated,
                        )
                        # safe all ids in deleted
                        deleted_instances[collection] = to_be_deleted[collection]

        # update lost references in bulk
        for collection, update_schema_part in update_schema.items():
            self.generic_update(
                events,
                collection,
                update_schema_part,
                to_be_updated[collection],
                deleted_instances,
            )

    def is_finished(self, deleted_instances: dict) -> bool:
        """Checks if all collections were handled for deletion."""
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
        to_be_updated: dict[str, dict[int, dict[str, list[int | str]]]],
    ) -> None:
        """
        Deletes all models noted by the collection_delete_schema.
        Marks all models for deletion noted by the fields in collection_delete_schema.
        Marks all models for update noted by the fields in collection_delete_schema.
        """
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
                assert foreign_collection != collection
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
                if "generic_" in foreign_field:
                    foreign_field = foreign_field.lstrip("generic_")
                    target_field_generic = True
                else:
                    target_field_generic = False
                if foreign_ids_field in model:
                    if "_ids" in foreign_ids_field:
                        foreign_ids = model[foreign_ids_field]
                    else:
                        foreign_ids = [model[foreign_ids_field]]
                    for foreign_id in foreign_ids:
                        if isinstance(foreign_id, str):
                            tmp_foreign_collection, foreign_id = (
                                collection_and_id_from_fqid(foreign_id)
                            )
                            # generic fields can have different collections in fqid thus differing from target collection.
                            # will be treated by the next combination of this field and collection
                            if tmp_foreign_collection != foreign_collection:
                                continue
                        # need to store own collection context for generic foreign field
                        if target_field_generic:
                            model_id_or_fqid: str | int = fqid_from_collection_and_id(
                                collection, model_id
                            )
                        else:
                            model_id_or_fqid = model_id
                        to_be_updated[foreign_collection][foreign_id][
                            foreign_field
                        ].append(model_id_or_fqid)

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
        collection_update_schema: list[str],
        to_be_updated_in_collection: dict[int, dict[str, Any]],
        deleted_instances: dict,
    ) -> None:
        """
        Updates all models of the collection with the info provided by the collection_update_schema
        but not those that were already deleted.
        """
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
                    collection_update_schema,
                )
            ]
        ).get(collection, {})
        for instance_id, fields_and_ids in to_be_updated_in_collection.items():
            instance = instances.get(instance_id, {})
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

    def subtract_ids(
        self, front_ids: list | None, without_ids: list | None
    ) -> list | None:
        """
        This subtracts items of a list from another list in an efficient manner.
        Returns a list.
        """
        if not front_ids:
            return None
        if not without_ids:
            return front_ids
        return list(set(front_ids) - set(without_ids)) or None
