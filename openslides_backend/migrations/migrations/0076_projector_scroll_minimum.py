from datastore.migrations import BaseModelMigration
from datastore.writer.core.write_request import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ...shared.filters import And, FilterOperator


class Migration(BaseModelMigration):
    """
    This migration sets scroll of projectors below the minimum of 0 to 0.
    """

    target_migration_index = 77

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        filter_ = And(
            FilterOperator("scroll", "<", 0),
            FilterOperator("meta_deleted", "!=", True),
        )
        projectors = self.reader.filter(
            "projector",
            filter_,
            ["scroll"],
        )
        return [
            RequestUpdateEvent(
                fqid_from_collection_and_id("projector", projector_id),
                {"scroll": 0},
            )
            for projector_id in projectors
        ]
