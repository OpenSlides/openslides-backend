from datastore.migrations import BaseModelMigration, MigrationException
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import (
    BaseRequestEvent,
    RequestDeleteEvent,
    RequestUpdateEvent,
)

from ...shared.filters import And, FilterOperator
from ..mixins.deletion_mixin import DeletionMixin, MigrationDeletionSchema


class Migration(BaseModelMigration, DeletionMixin):
    """
    This migration removes all relations to and the statute motions/paragraphs themselves.
    This requires to also delete all dangling models. However, lead motions, poll candidate lists
    and their candidates of deleted polls will not be deleted since they are not expected
    in this context.
    """

    target_migration_index = 60

    deletion_schema: MigrationDeletionSchema = {
        "motion": {
            "deletes_models_from": {
                "motion_change_recommendation": ["change_recommendation_ids"],
                "motion_comment": ["comment_ids"],
                "personal_note": ["personal_note_ids"],
                "motion_working_group_speaker": ["working_group_speaker_ids"],
                "motion_editor": ["editor_ids"],
                "motion_submitter": ["submitter_ids"],
                "list_of_speakers": ["list_of_speakers_id"],
                "agenda_item": ["agenda_item_id"],
                "projection": ["projection_ids"],
                "poll": ["poll_ids"],
                "motion": [
                    "amendment_ids",
                    "origin_id",
                    "derived_motion_ids",
                    "all_origin_ids",
                    "all_derived_motion_ids",
                ],
            },
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "motion_ids",
                },
                "tag": {
                    "tag_ids": "generic-tagged_ids",
                },
                "motion_state": {
                    "state_id": "motion_ids",
                    "recommendation_id": "motion_recommendation_ids",
                },
                "motion": {
                    "origin_meeting_id": "forwarded_motion_ids",
                    "sort_parent_id": "sort_child_ids",
                    "sort_child_ids": "sort_parent_id",
                    "state_extension_reference_ids": "referenced_in_motion_state_extension_ids",
                    "referenced_in_motion_state_extension_ids": "state_extension_reference_ids",
                    "recommendation_extension_reference_ids": "referenced_in_motion_recommendation_extension_ids",
                    "referenced_in_motion_recommendation_extension_ids": "recommendation_extension_reference_ids",
                },
                "motion_category": {
                    "category_id": "motion_ids",
                },
                "motion_block": {
                    "block_id": "motion_ids",
                },
                "meeting_user": {
                    "supporter_meeting_user_ids": "supported_motion_ids",
                },
                "meeting_mediafile": {
                    "attachment_meeting_mediafile_ids": "generic-attachment_ids",
                },
            },
        },
        "motion_submitter": {
            "deletes_models_from": {},
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "motion_submitter_ids",
                },
                "meeting_user": {
                    "meeting_user_id": "motion_submitter_ids",
                },
            },
        },
        "motion_editor": {
            "deletes_models_from": {},
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "motion_editor_ids",
                },
                "meeting_user": {
                    "meeting_user_id": "motion_editor_ids",
                },
            },
        },
        "motion_working_group_speaker": {
            "deletes_models_from": {},
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "motion_working_group_speaker_ids",
                },
                "meeting_user": {
                    "meeting_user_id": "motion_working_group_speaker_ids",
                },
            },
        },
        "personal_note": {
            "deletes_models_from": {},
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "personal_note_ids",
                },
                "meeting_user": {
                    "meeting_user_id": "personal_note_ids",
                },
            },
        },
        "motion_comment": {
            "deletes_models_from": {},
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "motion_comment_ids",
                },
                "motion_comment_section": {
                    "section_id": "comment_ids",
                },
            },
        },
        "motion_comment_section": {
            "deletes_models_from": {},
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "motion_comment_section_ids",
                },
            },
        },
        "motion_change_recommendation": {
            "deletes_models_from": {},
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "motion_change_recommendation_ids",
                },
            },
        },
        "poll": {
            "deletes_models_from": {
                "option": ["option_ids"],
                "projection": ["projection_ids"],
            },
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "poll_ids",
                },
                "group": {
                    "entitled_group_ids": "poll_ids",
                },
                "user": {
                    "voted_ids": "poll_voted_ids",
                },
            },
        },
        "option": {
            "deletes_models_from": {
                "vote": ["vote_ids"],
            },
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "option_ids",
                },
                "motion": {
                    "content_object_id": "option_ids",
                },
                "poll_candidate_list": {
                    "content_object_id": "option_id",
                },
                "user": {
                    "content_object_id": "option_ids",
                },
            },
        },
        "vote": {
            "deletes_models_from": {},
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "vote_ids",
                },
                "user": {
                    "user_id": "vote_ids",
                    "delegated_user_id": "delegated_vote_ids",
                },
            },
        },
        "agenda_item": {
            "deletes_models_from": {
                "projection": ["projection_ids"],
            },
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "agenda_item_ids",
                },
                "agenda_item": {
                    "parent_id": "child_ids",
                    "child_ids": "parent_id",
                },
                "tag": {
                    "tag_ids": "generic-tagged_ids",
                },
            },
        },
        "list_of_speakers": {
            "deletes_models_from": {
                "projection": ["projection_ids"],
                "speaker": ["speaker_ids"],
                "structure_level_list_of_speakers": [
                    "structure_level_list_of_speakers_ids"
                ],
            },
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "list_of_speakers_ids",
                },
            },
        },
        "speaker": {
            "deletes_models_from": {},
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "speaker_ids",
                },
                "meeting_user": {
                    "meeting_user_id": "speaker_ids",
                },
                "point_of_order_category": {
                    "point_of_order_category_id": "speaker_ids",
                },
            },
        },
        "structure_level_list_of_speakers": {
            "deletes_models_from": {},
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "structure_level_list_of_speakers_ids",
                },
                "meeting_user": {
                    "meeting_user_ids": "structure_level_list_of_speakers_ids",
                },
                "structure_level": {
                    "structure_level_id": "structure_level_list_of_speakers_ids",
                },
            },
        },
        "structure_level": {
            "deletes_models_from": {},
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "structure_level_ids",  # TODO check in test # maybe test already corrupt?
                },
                "meeting_user": {
                    "meeting_user_ids": "structure_level_ids",
                },
            },
        },
        "projection": {
            "deletes_models_from": {},
            "updates_models_from": {
                "meeting": {
                    "meeting_id": "all_projection_ids",
                },
                "projector": {
                    "current_projector_id": "current_projection_ids",
                    "preview_projector_id": "preview_projection_ids",
                    "history_projector_id": "history_projection_ids",
                },
            },
        },
    }

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        """Migrates all models by deleting everything related to statutes and updating the relations."""
        events: list[BaseRequestEvent] = []

        # delete statute related motions cascadingly and update related
        statute_motions = self.reader.filter(
            "motion",
            And(
                FilterOperator("statute_paragraph_id", "!=", None),
                FilterOperator("meta_deleted", "!=", True),
            ),
        )
        for motion in statute_motions.values():
            if motion.get("lead_motion_id"):
                raise MigrationException("A statute motion cannot have a lead motion.")
        self.delete_update_by_schema(
            {"motion": {motion_id for motion_id, motion in statute_motions.items()}},
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
