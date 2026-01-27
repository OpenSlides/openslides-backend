from datastore.migrations import BaseModelMigration
from datastore.writer.core.write_request import (
    BaseRequestEvent,
    RequestDeleteEvent,
    RequestUpdateEvent,
)

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ...shared.filters import And, FilterOperator, Not, Or


class Migration(BaseModelMigration):
    """
    This migration recreates relations between projection and its content_object.
    Deletes the projection if no model can be found.
    """

    target_migration_index = 76

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        filter_ = And(
            FilterOperator("content_object_id", "=", None),
            FilterOperator("meta_deleted", "!=", True),
        )
        empty_projections = self.reader.filter(
            "projection",
            filter_,
            ["content_object_id"],
        )
        filled_projections = set()
        # pa = possibly affected
        pa_collections = [
            "meeting",
            "motion",
            "meeting_mediafile",
            "list_of_speakers",
            "motion_block",
            "assignment",
            "agenda_item",
            "topic",
            "poll",
            "projector_message",
            "projector_countdown",
        ]
        for pa_collection in pa_collections:
            filter_ = And(
                Not(
                    Or(
                        FilterOperator("projection_ids", "=", None),
                        FilterOperator("projection_ids", "=", "[]"),
                    )
                ),
                FilterOperator("meta_deleted", "!=", True),
            )
            pa_models = self.reader.filter(
                pa_collection,
                filter_,
                ["projection_ids"],
            )
            for pa_model_id, pa_model in pa_models.items():
                for projection_id in (
                    projection_ids := pa_model.get("projection_ids", [])
                ):
                    if projection_id in empty_projections:
                        events.append(
                            RequestUpdateEvent(
                                fqid_from_collection_and_id(
                                    "projection", projection_id
                                ),
                                {
                                    "content_object_id": fqid_from_collection_and_id(
                                        pa_collection, pa_model_id
                                    )
                                },
                            )
                        )
                        filled_projections.add(projection_id)
                    else:
                        projection_ids.remove(projection_id)
                        events.append(
                            RequestUpdateEvent(
                                fqid_from_collection_and_id(pa_collection, pa_model_id),
                                {"projection_ids": projection_ids},
                            )
                        )
        for id_ in empty_projections:
            if id_ not in filled_projections:
                events.append(
                    RequestDeleteEvent(fqid_from_collection_and_id("projection", id_))
                )
        return events
