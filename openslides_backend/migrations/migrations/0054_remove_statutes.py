from collections import defaultdict

from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import (
    BaseRequestEvent,
    RequestDeleteEvent,
    RequestUpdateEvent,
)


class Migration(BaseModelMigration):
    """
    This migration removes all relations to and the statute motions/paragraphs themselves. This requieres to also delete all dangling models.
    """

    target_migration_index = 55

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
            "meeting_user_field": "motion_submitter_ids"
        },
        {
            "field": "editor_ids",
            "collection": "motion_editor",
            "meeting_field": "motion_editor_ids",
            "meeting_user_field": "editor_ids"
        },
        {
            "field": "working_group_speaker_ids",
            "collection": "motion_working_group_speaker",
            "meeting_field": "motion_working_group_speaker_ids",
            "meeting_user_field": "motion_working_group_speaker_ids"
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
            "meeting_user_field": "personal_note_ids"
        },
    ]

    def subtract_ids(self, lhs_ids: list | None, rhs_ids: list | None) -> list | None:
        """
        this hopefully subtracts a list of a list in an efficient manner
        """
        if lhs_ids is None or lhs_ids == []:
            return None
        if rhs_ids is None or rhs_ids == []:
            return lhs_ids
        lhs_ids = list(set(lhs_ids) - set(rhs_ids))
        if lhs_ids == []:
            return None
        return lhs_ids

    def delete_projections(
        self,
        projection_ids: list[int],
        events: list[BaseRequestEvent],
        meeting_id: int,
        to_remove_in_meetings: defaultdict[int, defaultdict[str, list]],
    ) -> None:
        """This deletes all projections and updates the content_object and projector"""
        for projection_id in projection_ids:
            projection_fqid = fqid_from_collection_and_id("projection", projection_id)
            projection = self.reader.get(
                projection_fqid,
                [
                    "current_projector_id",
                    "preview_projector_id",
                    "history_projector_id",
                    "content_object_id",
                ],
            )
            if projector_id := projection.get("current_projector_id", ""):
                if response := self.update_relations(
                    fqid_from_collection_and_id("projector", projector_id),
                    "current_projection_ids",
                    projection_id,
                ):
                    events.append(response)
            if projector_id := projection.get("preview_projector_id", ""):
                if response := self.update_relations(
                    fqid_from_collection_and_id("projector", projector_id),
                    "preview_projection_ids",
                    projection_id,
                ):
                    events.append(response)
            if projector_id := projection.get("history_projector_id", ""):
                if response := self.update_relations(
                    fqid_from_collection_and_id("projector", projector_id),
                    "history_projection_ids",
                    projection_id,
                ):
                    events.append(response)
            content_object_fqid = projection.get("content_object_id", "")
            if response := self.update_relations(
                content_object_fqid, "projection_ids", projection_id
            ):
                events.append(response)
            events.append(RequestDeleteEvent(projection_fqid))
            to_remove_in_meetings[meeting_id]["projection_ids"].append(projection_id)

    def update_relations(
        self,
        fqid: str,
        foreign_field: str,
        deleted_ids: int | set | list,
        origin_collection: str | None = None,
    ) -> RequestUpdateEvent | None:
        """
        This updates the relations in the by fqid given object in the foreign_field by subtracting the deleted ids
        The origin_collection is needed if the foreign field is generic.
        """
        model = self.reader.get(fqid, [foreign_field])
        if field_value := model.get(foreign_field, []):
            if isinstance(deleted_ids, list):
                deleted_ids = set(deleted_ids)
            if isinstance(deleted_ids, set):
                # if target field is generic, convert to fqids
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
            else:
                field_value = field_value.remove(deleted_ids)
            if field_value == []:
                field_value = None
            return RequestUpdateEvent(fqid, {foreign_field: field_value})
        return None

    def list_update(
        self, motion: dict, deleted_motions_ids: list, events: list
    ) -> None:
        """updates models related with motion"""
        for entry in self.motion_reference_id_list_update:
            field_name = entry.get("field", "")
            foreign_field = entry.get("foreign_field", "")
            collection_name = entry.get("collection", "")
            if field_value := motion.get(field_name):
                if isinstance(field_value, list):
                    for model_id in field_value:
                        if isinstance(model_id, int):
                            if (
                                collection_name == "motion"
                                and model_id in deleted_motions_ids
                            ):
                                continue
                        elif int(model_id.split("/")[1]) in deleted_motions_ids:
                            continue
                        if isinstance(model_id, int):
                            fqid = fqid_from_collection_and_id(
                                collection_name, model_id
                            )
                        else:
                            fqid = model_id
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
        deleted_motions_ids: list,
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
                            "meeting_user",
                            model.get("meeting_user_id", 0)
                        )
                        meeting_users_to_update[meeting_user_fqid][meeting_user_field].append(model_id)

    def update_polls(
        self,
        poll_ids_to_migrate: list,
        to_remove_in_meetings: defaultdict[int, defaultdict[str, list]],
        meeting_id: int,
        events: list,
    ) -> None:
        """deletes all polls and its subitems in motion"""
        for poll_id in poll_ids_to_migrate:
            poll_fqid = fqid_from_collection_and_id("poll", poll_id)
            poll = self.reader.get(
                poll_fqid,
                [
                    "content_object_id",
                    "option_ids",
                    "global_option_id",
                    "voted_ids",
                    "entitled_group_ids",
                    "projection_ids",
                ],
            )
            option_ids = poll.get("option_ids", [])
            # option_ids.append(poll.get("global_option_id"))
            for option_id in option_ids:
                option_fqid = fqid_from_collection_and_id("option", option_id)
                option = self.reader.get(
                    option_fqid, ["vote_ids", "content_object_id", "meeting_id"]
                )
                vote_ids = option.get("vote_ids", [])
                for vote_id in vote_ids:
                    # TODO collect users do one update_relations after this loop for each user?
                    vote_fqid = fqid_from_collection_and_id("vote", vote_id)
                    vote = self.reader.get(vote_fqid, ["user_id", "delegated_user_id"])
                    vote = self.reader.get(fqid_from_collection_and_id("vote", vote_id))
                    if response := self.update_relations(
                        fqid_from_collection_and_id("user", vote.get("user_id", 0)),
                        "vote_ids",
                        vote_id,
                    ):
                        events.append(response)
                    if response := self.update_relations(
                        fqid_from_collection_and_id(
                            "user", vote.get("delegated_user_id", 0)
                        ),
                        "delegated_vote_ids",
                        vote_id,
                    ):
                        events.append(response)
                    to_remove_in_meetings[meeting_id]["vote_ids"].append(vote_id)
                    events.append(RequestDeleteEvent(vote_fqid))
                content_object_fqid = option.get("content_object_id", "")
                if "poll_candidate_list" in content_object_fqid:
                    foreign_field = "option_id"
                else:
                    foreign_field = "option_ids"
                if response := self.update_relations(
                    content_object_fqid, foreign_field, option_id
                ):
                    events.append(response)
                events.append(RequestDeleteEvent(option_fqid))
                to_remove_in_meetings[meeting_id]["option_ids"].append(option_id)
            # back to polls
            self.delete_projections(
                poll.get("projection_ids", ""),
                events,
                meeting_id,
                to_remove_in_meetings,
            )

            voted_ids = poll.get("voted_ids", "")
            for voted_id in voted_ids:
                if response := self.update_relations(
                    fqid_from_collection_and_id("user", voted_id),
                    "poll_voted_ids",
                    poll_id,
                ):
                    events.append(response)
            group_ids = poll.get("entitled_group_ids", "")
            for group_id in group_ids:
                if response := self.update_relations(
                    fqid_from_collection_and_id("group", group_id),
                    "poll_ids",
                    poll_id,
                ):
                    events.append(response)
            to_remove_in_meetings[meeting_id]["poll_ids"].append(poll_id)
            events.append(RequestDeleteEvent(poll_fqid))

    def update_agenda_item(
        self,
        agenda_item_id: int,
        tags_to_update: defaultdict[int, list],
        to_remove_in_meetings: defaultdict[int, defaultdict[str, list]],
        meeting_id: int,
        events: list,
    ) -> None:
        """
        deletes agenda item in motion and all its subitems
        acutal delete request will be created in meeting update
        """
        if agenda_item_id:
            agenda_item_fqid = fqid_from_collection_and_id(
                "agenda_item", agenda_item_id
            )
            agenda_item = self.reader.get(
                agenda_item_fqid,
                [
                    "parent_id",
                    "child_ids",
                    "tag_ids",
                    "projection_ids",
                ],
            )
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
                tags_to_update[tag_id].append(agenda_item_fqid)
                # if response := self.update_relations(
                #     fqid_from_collection_and_id("tag", tag_id),
                #     "tagged_ids",
                #     [agenda_item_id],
                #     "agenda_item"
                # ):
                # events.append(response)
                # to_remove_in_meetings[meeting_id]["tag"].append(tag_id)
            self.delete_projections(
                agenda_item.get("projection_ids", ""),
                events,
                meeting_id,
                to_remove_in_meetings,
            )
            to_remove_in_meetings[meeting_id]["agenda_item_ids"].append(agenda_item_id)

    def update_list_of_speakers(
        self,
        list_of_speakers_id: int,
        to_remove_in_meetings: defaultdict[int, defaultdict[str, list]],
        meeting_id: int,
        events: list,
    ) -> None:
        """deletes list of speakers in motion and all its subitems"""
        if list_of_speakers_id:
            los_fqid = fqid_from_collection_and_id(
                "list_of_speakers", list_of_speakers_id
            )
            list_of_speakers = self.reader.get(
                los_fqid,
                [
                    "content_object_id",
                    "speaker_ids",
                    "structure_level_list_of_speakers_ids",
                    "projection_ids",
                ],
            )
            speaker_ids = list_of_speakers.get("speaker_ids", "")
            for speaker_id in speaker_ids:
                speaker_fqid = fqid_from_collection_and_id("speaker", speaker_id)
                speaker = self.reader.get(
                    speaker_fqid,
                    [
                        "meeting_user_id",
                        "point_of_order_category_id",
                        "meeting_id",
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
                structure_level_los = self.reader.get(
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
            self.delete_projections(
                list_of_speakers.get("projection_ids", ""),
                events,
                meeting_id,
                to_remove_in_meetings,
            )
            to_remove_in_meetings[meeting_id]["list_of_speakers_ids"].append(
                list_of_speakers_id
            )
            events.append(RequestDeleteEvent(los_fqid))

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        to_remove_in_meetings: defaultdict[int, defaultdict[str, list]] = defaultdict(
            lambda: defaultdict(list)
        )
        tags_to_update: defaultdict[int, list] = defaultdict(list)
        meeting_users_to_update: defaultdict[str, defaultdict[str, list]] = defaultdict(
            lambda: defaultdict(list))

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

        # find statute related motions
        motions = self.reader.get_all("motion", ["statute_paragraph_id", "meeting_id"])
        for motion_id, motion in motions.items():
            if motion.get("statute_paragraph_id", ""):  # unnecessary?
                # will delete motions later when updating meeting to prevent ModelDoesNotExist errors.
                to_remove_in_meetings[motion.get("meeting_id", 0)]["motion_ids"].append(
                    motion_id
                )
        # update and delete motion related models
        for meeting_id, to_remove_dict in to_remove_in_meetings.items():
            deleted_motions_ids = to_remove_dict.get("motion_ids", [])
            for motion_id in deleted_motions_ids:
                motion_fqid = fqid_from_collection_and_id("motion", motion_id)
                motion = self.reader.get(motion_fqid)
                meeting_id = motion.get("meeting_id", "")

                self.list_update(motion, deleted_motions_ids, events)
                self.list_delete(
                    motion,
                    deleted_motions_ids,
                    to_remove_in_meetings,
                    meeting_users_to_update,
                    meeting_id,
                    events,
                )

                self.delete_projections(
                    motion.get("projection_ids", ""),
                    events,
                    meeting_id,
                    to_remove_in_meetings,
                )

                # delete cascading models related with motion
                self.update_polls(
                    motion.get("poll_ids", []),
                    to_remove_in_meetings,
                    meeting_id,
                    events,
                )
                self.update_agenda_item(
                    motion.get("agenda_item_id", 0),
                    tags_to_update,
                    to_remove_in_meetings,
                    meeting_id,
                    events,
                )
                self.update_list_of_speakers(
                    motion.get("list_of_speakers_id", 0),
                    to_remove_in_meetings,
                    meeting_id,
                    events,
                )

                if tag_ids := motion.get("tag_ids", []):
                    for tag_id in tag_ids:
                        tags_to_update[tag_id].append(motion_fqid)
                events.append(
                    RequestDeleteEvent(fqid_from_collection_and_id("motion", motion_id))
                )

        for meeting_users_fqid, field_default_dict in meeting_users_to_update.items():
            meeting_user = self.reader.get(meeting_users_fqid)
            meeting_user_fields = {}
            for field_name, ids_to_delete in field_default_dict.items():
                field_value = meeting_user.get(field_name)
                field_value = self.subtract_ids(field_value, ids_to_delete)
                meeting_user_fields[field_name] = field_value
            events.append(
                RequestUpdateEvent(
                    meeting_users_fqid,
                    meeting_user_fields
                )
            )

        for tag_id, object_list in tags_to_update.items():
            if response := self.update_relations(
                fqid_from_collection_and_id("tag", tag_id),
                "tagged_ids",
                object_list,
                "agenda_item",
            ):
                events.append(response)

        # find and update statute related motion workflows
        motion_workflows = self.reader.get_all(
            "motion_workflow", ["default_statute_amendment_workflow_meeting_id"]
        )
        for workflow_id, workflow in motion_workflows.items():
            events.append(
                RequestUpdateEvent(
                    fqid_from_collection_and_id("motion_workflow", workflow_id),
                    {"default_statute_amendment_workflow_meeting_id": None},
                )
            )

        # update meetings TODO check if more updates needed
        meetings = self.reader.get_all(
            "meeting",
            [
                "motion_statute_paragraph_ids",
                "forwarded_motion_ids",
                "motion_ids",
                "motions_statutes_enabled",
                "motions_statute_recommendations_by",
                "motion_statute_paragraph_ids",
                "motions_default_statute_amendment_workflow_id",
                "list_of_speakers_ids",
                "structure_level_list_of_speakers_ids",
                "speaker_ids",
                "poll_ids",
                "agenda_item_ids",
                "option_ids",
                "vote_ids",
                "all_projection_ids",
                "statute_paragraph_ids",
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

            statute_paragraph_ids = self.subtract_ids(
                meeting.get("motion_statute_paragraph_ids"),
                to_remove_in_meetings[meeting_id].get("statute_paragraph_ids"),
            )
            motion_ids = self.subtract_ids(
                meeting.get("motion_ids"),
                to_remove_in_meetings[meeting_id].get("motion_ids"),
            )
            forwarded_motion_ids = self.subtract_ids(
                meeting.get("forwarded_motion_ids"),
                to_remove_in_meetings[meeting_id].get("forwarded_motion_ids"),
            )
            list_of_speakers_ids = self.subtract_ids(
                meeting.get("list_of_speakers_ids"),
                to_remove_in_meetings[meeting_id].get("list_of_speakers_ids"),
            )
            structure_level_los_ids = self.subtract_ids(
                meeting.get("structure_level_list_of_speakers_ids"),
                to_remove_in_meetings[meeting_id].get("structure_level_los_ids"),
            )
            speaker_ids = self.subtract_ids(
                meeting.get("speaker_ids"),
                to_remove_in_meetings[meeting_id].get("speaker_ids"),
            )
            poll_ids = self.subtract_ids(
                meeting.get("poll_ids"),
                to_remove_in_meetings[meeting_id].get("poll_ids"),
            )
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
            option_ids = self.subtract_ids(
                meeting.get("option_ids"),
                to_remove_in_meetings[meeting_id].get("option_ids"),
            )
            vote_ids = self.subtract_ids(
                meeting.get("vote_ids"),
                to_remove_in_meetings[meeting_id].get("vote_ids"),
            )
            projection_ids = self.subtract_ids(
                meeting.get("all_projection_ids"),
                to_remove_in_meetings[meeting_id].get("projection_ids"),
            )

            events.append(
                RequestUpdateEvent(
                    meeting_fqid,
                    {
                        "motion_ids": motion_ids,
                        "forwarded_motion_ids": forwarded_motion_ids,
                        "motions_statutes_enabled": None,
                        "motions_statute_recommendations_by": None,
                        "motion_statute_paragraph_ids": None,
                        "motions_default_statute_amendment_workflow_id": None,
                        "list_of_speakers_ids": list_of_speakers_ids,
                        "structure_level_list_of_speakers_ids": structure_level_los_ids,
                        "speaker_ids": speaker_ids,
                        "poll_ids": poll_ids,
                        "agenda_item_ids": agenda_item_ids,
                        "option_ids": option_ids,
                        "vote_ids": vote_ids,
                        "all_projection_ids": projection_ids,
                        "statute_paragraph_ids": statute_paragraph_ids,  # TODO checked in tests?
                        **additional_meeting_update_fields,
                    },
                )
            )
        return events
