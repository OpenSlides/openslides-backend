from collections import defaultdict
from typing import Any

from datastore.migrations import BaseModelMigration
from datastore.reader.core.requests import GetManyRequestPart
from datastore.shared.util import fqid_from_collection_and_id, collection_and_id_from_fqid
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
        "option_ids",
        "vote_ids",
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
                events, collection, update_schema_part, self.to_be_updated[collection], self.deleted_instances
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
                # will delete motions later when updating meeting to prevent ModelDoesNotExist errors.
                to_remove_in_meetings[motion.get("meeting_id", 0)]["motion_ids"].append(
                    motion_id
                )

        # update and delete motion related models
        to_delete_polls = []
        to_delete_agenda_item_ids = []
        to_delete_los_ids = []
        to_delete_projection_ids = []
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

                if projection_ids := motion.get("projection_ids", []):
                    for projection_id in projection_ids:
                        to_delete_projection_ids.append(projection_id)

                # collect models cascading delete to other models
                if poll_ids := motion.get("poll_ids", []):
                    for poll_id in poll_ids:
                        to_delete_polls.append(poll_id)
                if agenda_item_id := motion.get("agenda_item_id", 0):
                    to_delete_agenda_item_ids.append(agenda_item_id)
                if list_of_speakers_id := motion.get("list_of_speakers_id", 0):
                    to_delete_los_ids.append(list_of_speakers_id)

                if tag_ids := motion.get("tag_ids", []):
                    for tag_id in tag_ids:
                        tags_to_update[tag_id].add(motion_fqid)
                events.append(
                    RequestDeleteEvent(fqid_from_collection_and_id("motion", motion_id))
                )
        # delete models cascading delete to other models
        self.delete_polls(
            to_delete_polls,
            to_remove_in_meetings,
            events,
            to_remove_in_projectors,
            to_remove_in_users,
            to_delete_projection_ids,
        )
        self.delete_agenda_items(
            to_delete_agenda_item_ids,
            tags_to_update,
            to_remove_in_meetings,
            events,
            to_remove_in_projectors,
            to_delete_projection_ids,
        )
        self.delete_lists_of_speakers(
            to_delete_los_ids,
            to_remove_in_meetings,
            events,
            to_remove_in_projectors,
            to_delete_projection_ids,
        )
        # cascaded deletes in bulk
        self.delete_projections(
            to_delete_projection_ids,
            events,
            to_remove_in_meetings,
            to_remove_in_projectors,
        )

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

    def delete_polls(
        self,
        poll_ids_to_migrate: list,
        to_remove_in_meetings: defaultdict[int, defaultdict[str, list]],
        events: list,
        to_remove_in_projectors: defaultdict[int, defaultdict[str, list]],
        to_remove_in_users: defaultdict[int, defaultdict[str, list]],
        to_delete_projection_ids: list[int],
    ) -> None:
        """deletes all polls and its subitems in motion"""
        deletion_schema: dict[str, dict[str, list[str]]] = {
            "meeting": {
                "precursors": [],
                "update_collections": [],
                "update_foreign_fields": [],
            },
            "poll": {
                "precursors": [],  # motion
                "cascaded_delete_collections": ["option"],  # projections
                "cascaded_delete_fields": ["option_ids"],
                "update_ids_fields": [],
                "update_collections": [],
                "update_foreign_fields": [],
            },
            "option": {
                "precursors": ["poll"],
                "cascaded_delete_collections": ["vote"],
                "cascaded_delete_fields": ["vote_ids"],
                "update_ids_fields": ["content_object_id", "content_object_id", "content_object_id"],
                "update_collections": ["motion", "poll_candidate_list", "user"],
                "update_foreign_fields": ["option_ids", "option_ids", "option_ids"],
            },
            "vote": {
                "precursors": ["option"],
                "cascaded_delete_collections": [],
                "cascaded_delete_fields": [],
                "update_ids_fields": ["meeting_id", "user_id", "delegated_user_id"],
                "update_collections": ["meeting", "user", "user"],
                "update_foreign_fields": ["vote_ids", "vote_ids", "delegated_vote_ids"],
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
                self.update_schema[collection].extend([collection_fields])
        to_be_deleted: dict[str, set] = {
            collection: set() for collection in deletion_schema.keys()
        }
        self.to_be_updated: dict[str, dict[str, list]] = {
            collection: defaultdict(lambda: defaultdict(list))  # collection : id : fields : values
            for collection in self.update_schema.keys()
        }
        # not needed if motion is part of this TODO delete
        to_be_deleted["poll"] = set(poll_ids_to_migrate)
        self.deleted_instances.update({"motion": {1}})
        self.to_be_updated.update({"motion": defaultdict(lambda: defaultdict(list))})

        # delete until all have at least empty list (means finished)
        while not self.is_finished(self.deleted_instances):
            for collection, schema_part in deletion_schema.items():
                # check precursors have finished
                if not any(
                    precursor
                    for precursor in schema_part["precursors"]
                    if self.deleted_instances[precursor] is None
                ):
                    self.generic_delete(
                        events, collection, schema_part, to_be_deleted, self.to_be_updated
                    )
                    # safe all ids in deleted
                    self.deleted_instances[collection] = to_be_deleted[collection]
        # update lost references in bulk
        # for collection, update_schema_part in update_schema.items():
        #     self.update(
        #         events, collection, update_schema_part, to_be_updated[collection]
        #     )

        polls = self.reader.get_many(
            [
                GetManyRequestPart(
                    "poll",
                    poll_ids_to_migrate,
                    [
                        "option_ids",
                        "global_option_id",
                        "voted_ids",
                        "entitled_group_ids",
                        "projection_ids",
                        "meeting_id",
                    ],
                )
            ]
        ).get("poll", {})
        for poll_id, poll in polls.items():
            meeting_id = poll["meeting_id"]
            # poll_fqid = fqid_from_collection_and_id("poll", poll_id)
            option_ids = poll.get(
                "option_ids", []
            )  # oder doch für alle meetings auf einen schlag? dict benutzen?
            options = self.reader.get_many(
                [
                    GetManyRequestPart(
                        "option",
                        option_ids,
                        [
                            "vote_ids",
                            "content_object_id",
                        ],
                    )
                ]
            ).get("option", {})
            for option_id, option in options.items():
                # option_fqid = fqid_from_collection_and_id("option", option_id)
                # vote_ids = option.get("vote_ids", [])
                # for vote_id in vote_ids:
                #     vote_fqid = fqid_from_collection_and_id("vote", vote_id)
                #     vote = self.reader.get(vote_fqid, ["user_id", "delegated_user_id"])
                #     to_remove_in_users[vote.get("user_id", 0)]["vote_ids"].append(
                #         vote_id
                #     )
                #     to_remove_in_users[vote.get("delegated_user_id", 0)][
                #         "delegated_vote_ids"
                #     ].append(vote_id)
                #     to_remove_in_meetings[meeting_id]["vote_ids"].append(vote_id)
                #     events.append(RequestDeleteEvent(vote_fqid))
                content_object_fqid = option.get("content_object_id", "")
                if "poll_candidate_list" in content_object_fqid:
                    foreign_field = "option_id"
                else:
                    foreign_field = "option_ids"
                # the motion will be deleted anyways
                if "motion" not in content_object_fqid and (
                    response := self.update_relations(
                        content_object_fqid, foreign_field, option_id
                    )
                ):
                    events.append(response)
                # events.append(RequestDeleteEvent(option_fqid))
                to_remove_in_meetings[meeting_id]["option_ids"].append(option_id)
            # back to polls
            to_delete_projection_ids.extend(poll.get("projection_ids", []))
            if voted_ids := poll.get("voted_ids", ""):
                for voted_id in voted_ids:
                    to_remove_in_users[voted_id]["poll_voted_ids"].append(poll_id)
            group_ids = poll.get("entitled_group_ids", "")
            for group_id in group_ids:
                if response := self.update_relations(
                    fqid_from_collection_and_id("group", group_id),
                    "poll_ids",
                    poll_id,
                ):
                    events.append(response)
            to_remove_in_meetings[meeting_id]["poll_ids"].append(poll_id)
            # events.append(RequestDeleteEvent(poll_fqid))

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
        # get many of model to be deleted
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
            # stage new instances for deletion
            for foreign_collection, own_field in zip(
                collection_delete_schema["cascaded_delete_collections"], collection_delete_schema["cascaded_delete_fields"]
            ):
                to_be_deleted[foreign_collection].update(
                    model[own_field]
                )
            # stage instance ids for removal
            for foreign_collection, foreign_ids_field, foreign_field in zip(
                collection_delete_schema["update_collections"],
                collection_delete_schema["update_ids_fields"],
                collection_delete_schema["update_foreign_fields"],
            ):
                if "_ids" in foreign_ids_field:
                    for foreign_id in model[foreign_ids_field]:
                        if isinstance(foreign_id, str):
                            foreign_id, foreign_collection = collection_and_id_from_fqid(foreign_id)
                        # to_be_updated[foreign_collection][foreign_id][
                        #     foreign_field
                        # ].extend(model_id)
                else:
                    if isinstance(model[foreign_ids_field], str):
                        foreign_collection, foreign_id = collection_and_id_from_fqid(model[foreign_ids_field])
                    else: 
                        foreign_id = model[foreign_ids_field]
                    # to_be_updated[foreign_collection][foreign_id][
                    #     foreign_field
                    # ] = [model_id]
                to_be_updated[foreign_collection][foreign_id][
                    foreign_field
                ].extend([model_id])
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
        deleted_instances: dict
    ) -> None:
        if collection == "user":
            pass
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
            # save the instances data without the deleted ids
            for field, ids in fields_and_ids.items():
                fields_and_ids[field] = self.subtract_ids(instance.get(field, []), ids)
            events.append(
                RequestUpdateEvent(
                    fqid_from_collection_and_id(collection, instance_id), fields_and_ids
                )
            )
            pass

    def delete_agenda_items(
        self,
        agenda_item_ids: list[int],
        tags_to_update: defaultdict[int, set[str]],
        to_remove_in_meetings: defaultdict[int, defaultdict[str, list]],
        events: list,
        to_remove_in_projectors: defaultdict[int, defaultdict[str, list]],
        to_delete_projection_ids: list[int],
    ) -> None:
        """
        The actual delete request for the agenda item will be created in meeting update.
        Deletes agenda items id in motion and all its subitems.
        The child items are implicitly moved to the root of the agenda.
        """
        if not agenda_item_ids:
            return
        agenda_items = self.reader.get_many(
            [
                GetManyRequestPart(
                    "agenda_item",
                    agenda_item_ids,
                    [
                        "parent_id",
                        "child_ids",
                        "tag_ids",
                        "projection_ids",
                        "meeting_id",
                    ],
                )
            ]
        ).get("agenda_item", {})
        for agenda_item_id, agenda_item in agenda_items.items():
            agenda_item_fqid = fqid_from_collection_and_id(
                "agenda_item", agenda_item_id
            )
            meeting_id = agenda_item["meeting_id"]
            child_ids = agenda_item.get("child_ids", "")
            if parent_id := agenda_item.get("parent_id"):
                if response := self.update_relations(
                    fqid_from_collection_and_id("agenda_item", parent_id),
                    "child_ids",
                    agenda_item_id,
                ):
                    events.append(response)
            for child_id in child_ids:
                events.append(
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("agenda_item", child_id),
                        {"parent_id": None},
                    )
                )
            tag_ids = agenda_item.get("tag_ids", [0])
            for tag_id in tag_ids:
                tags_to_update[tag_id].add(agenda_item_fqid)
            to_delete_projection_ids.extend(agenda_item.get("projection_ids", []))
            to_remove_in_meetings[meeting_id]["agenda_item_ids"].append(agenda_item_id)

    def delete_lists_of_speakers(
        self,
        list_of_speakers_ids: list[int],
        to_remove_in_meetings: defaultdict[int, defaultdict[str, list]],
        events: list,
        to_remove_in_projectors: defaultdict[int, defaultdict[str, list]],
        to_delete_projection_ids: list[int],
    ) -> None:
        """deletes list of speakers in motion and all its subitems"""
        if not list_of_speakers_ids:
            return
        lists_of_speakers = self.reader.get_many(
            [
                GetManyRequestPart(
                    "list_of_speakers",
                    list_of_speakers_ids,
                    [
                        "content_object_id",
                        "speaker_ids",
                        "structure_level_list_of_speakers_ids",
                        "projection_ids",
                        "meeting_id",
                    ],
                )
            ]
        ).get("list_of_speakers", {})
        for list_of_speakers_id, list_of_speakers in lists_of_speakers.items():
            meeting_id = list_of_speakers["meeting_id"]
            los_fqid = fqid_from_collection_and_id(
                "list_of_speakers", list_of_speakers_id
            )
            speaker_ids = list_of_speakers.get("speaker_ids", "")
            for speaker_id in speaker_ids:
                speaker_fqid = fqid_from_collection_and_id("speaker", speaker_id)
                speaker = self.reader.get(  # TODO get many
                    speaker_fqid,
                    [
                        "meeting_user_id",
                        "point_of_order_category_id",
                        "meeting_id",  # nötig wenn todo oberhalb erledigt?
                    ],
                )
                meeting_user_id = speaker.get("meeting_user_id", "")
                if response := self.update_relations(
                    fqid_from_collection_and_id("meeting_user", meeting_user_id),
                    "speaker_ids",
                    speaker_id,
                ):
                    events.append(response)
                point_of_order_category_id = speaker.get(
                    "point_of_order_category_id", ""
                )
                if response := self.update_relations(
                    fqid_from_collection_and_id(
                        "point_of_order_category",
                        point_of_order_category_id,
                    ),
                    "speaker_ids",
                    (speaker_id),
                ):
                    events.append(response)
                to_remove_in_meetings[meeting_id]["speaker_ids"].append(speaker_id)
                events.append(RequestDeleteEvent(speaker_fqid))
            structure_level_los_ids = list_of_speakers.get(
                "structure_level_list_of_speakers_ids", ""
            )
            for structure_level_los_id in structure_level_los_ids:
                structure_level_los_fqid = fqid_from_collection_and_id(
                    "structure_level_list_of_speakers",
                    structure_level_los_id,
                )
                structure_level_los = self.reader.get(  # TODO get many
                    structure_level_los_fqid, ["structure_level_id"]
                )
                structure_level_id = structure_level_los.get("structure_level_id", 0)
                if response := self.update_relations(
                    fqid_from_collection_and_id("structure_level", structure_level_id),
                    "structure_level_list_of_speakers_ids",
                    structure_level_los_id,
                ):
                    events.append(response)
                to_remove_in_meetings[meeting_id]["structure_level_los_ids"].append(
                    structure_level_los_id
                )
                events.append(RequestDeleteEvent(structure_level_los_fqid))
            to_delete_projection_ids.extend(list_of_speakers.get("projection_ids", ""))
            to_remove_in_meetings[meeting_id]["list_of_speakers_ids"].append(
                list_of_speakers_id
            )
            events.append(RequestDeleteEvent(los_fqid))

    def delete_projections(
        self,
        projection_ids: list[int],
        events: list[BaseRequestEvent],
        to_remove_in_meetings: defaultdict[int, defaultdict[str, list]],
        to_remove_in_projectors: defaultdict[int, defaultdict[str, list]],
    ) -> None:
        """This deletes all projections and updates the content_object and projector"""
        projections = self.reader.get_many(
            [
                GetManyRequestPart(
                    "projection",
                    projection_ids,
                    [
                        "current_projector_id",
                        "preview_projector_id",
                        "history_projector_id",
                        "content_object_id",
                        "meeting_id",
                    ],
                )
            ]
        ).get("projection", {})
        for projection_id, projection in projections.items():
            meeting_id = projection["meeting_id"]
            for state in ["current", "preview", "history"]:
                if projector_id := projection.get(f"{state}_projector_id", ""):
                    to_remove_in_projectors[projector_id][
                        f"{state}_projection_ids"
                    ].append(projection_id)
            events.append(
                RequestDeleteEvent(
                    fqid_from_collection_and_id("projection", projection_id)
                )
            )
            to_remove_in_meetings[meeting_id]["projection_ids"].append(projection_id)

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
