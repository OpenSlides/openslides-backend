from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent


class Migration(BaseModelMigration):
    """
    This migration removes the forwarding user relation
    """

    target_migration_index = 55

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        for collection, field in [
            ("user", "forwarding_committee_ids"),
            ("committee", "forwarding_user_id"),
        ]:
            data = self.reader.get_all(collection, ["id", field])
            for id_, model in data.items():
                if field in model:
                    events.append(
                        RequestUpdateEvent(
                            fqid_from_collection_and_id(collection, id_),
                            {field: None},
                        )
                    )
        return events
