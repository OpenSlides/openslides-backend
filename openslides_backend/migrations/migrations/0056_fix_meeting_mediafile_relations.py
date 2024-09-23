
from datastore.migrations import BaseModelMigration
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ...shared.filters import And, FilterOperator, Or


class Migration(BaseModelMigration):
    """
    This migration fixes some fields that were not rewritten in migration 54
    """

    target_migration_index = 57
    old_group_fields = [
        "mediafile_access_group_ids",
        "mediafile_inherited_access_group_ids",
    ]

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        groups = self.reader.filter(
            "group",
            And(
                Or(
                    FilterOperator(field, "!=", None) for field in self.old_group_fields
                ),
                FilterOperator("meta_deleted", "!=", True),
            ),
            [*self.old_group_fields],
        )
        return [
            RequestUpdateEvent(
                fqid_from_collection_and_id("group", id_),
                {field: None for field in self.old_group_fields},
                {
                    "add": {
                        "meeting_" + field: group.get(field, [])
                        for field in self.old_group_fields
                    }
                },
            )
            for id_, group in groups.items()
        ]
