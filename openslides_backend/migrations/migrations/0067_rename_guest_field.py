from datastore.migrations import BaseModelMigration
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ...shared.filters import And, FilterOperator


class Migration(BaseModelMigration):
    """
    This migration renames:
    user/guest
    into
    user/external.
    This is needed to have a consistent naming of the field.
    """

    target_migration_index = 68

    collection = "user"
    old_field = "guest"
    new_field = "external"

    def migrate_models(self) -> list[BaseRequestEvent]:
        db_models = self.reader.filter(
            collection=self.collection,
            filter=And(
                FilterOperator(self.old_field, "!=", None),
                FilterOperator("meta_deleted", "!=", True),
            ),
        )

        return [
            RequestUpdateEvent(
                fqid_from_collection_and_id(self.collection, id),
                {
                    self.old_field: None,
                    self.new_field: model.get(self.old_field),
                },
            )
            for id, model in db_models.items()
        ]
