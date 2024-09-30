from datastore.migrations import BaseModelMigration, MigrationException
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import (
    BaseRequestEvent,
    RequestDeleteEvent,
    RequestUpdateEvent,
)

from ..mixins.deletion_mixin import DeletionMixin
from ...shared.filters import FilterOperator


class Migration(BaseModelMigration, DeletionMixin):
    """
    This migration removes all relations to and the statute motions/paragraphs themselves. This requieres to also delete all dangling models.
    Poll candidate lists and their candidates of deleted polls will not be deleted since they are not expected in this context.
    """

    target_migration_index = 57

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
                "motion",
                "motion",
                "motion",
                "motion",
                "motion",
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
                "amendment_ids",
                "origin_id",
                "derived_motion_ids",
                "all_origin_ids",
                "all_derived_motion_ids",
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
                "origin_meeting_id",
                "sort_parent_id",
                "sort_child_ids",
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
                "forwarded_motion_ids",
                "sort_child_ids",
                "sort_parent_id",
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
        """Migrates all models by deleting everything related to statutes and updating the relations."""
        events: list[BaseRequestEvent] = []

        # delete statute related motions cascadingly and update related
        statute_motions = self.reader.filter(
                "motion",
                FilterOperator("statute_paragraph_id", "!=", None)
        )
        for motion in statute_motions.values():
            if motion.get("lead_motion_id"):
                raise MigrationException("A statute motion cannot have a lead motion.")
            if motion.get("identical_motion_ids"):
                raise MigrationException("A statute motion cannot have a identic motion.")
        self.delete_update_by_schema(
            {
                "motion": {
                    motion_id
                    for motion_id, motion in statute_motions.items()
                }
            },
            self.deletion_schema,
            events,
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

        return events
